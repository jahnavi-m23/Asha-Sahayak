# backend/routes/ai.py
"""
Phase 2 AI and Safety API Routes for ASHA SAHAYAK.
Provides endpoints for:
- Processing Phase 1 transcripts (multilingual understanding, structured extraction, danger signs)
- Voice readback via Gnani Timbre v3.0
- Voice correction of individual fields
- Explicit record confirmation and handoff to Phase 3
- WebSocket for real-time interaction
- Inspection of public health danger sign rules
"""
import uuid
import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from pydantic import BaseModel, Field

from backend.models.schemas import (
    Phase1TranscriptInput,
    FieldExtractionOutput,
    CorrectionRequest,
    ConfirmationRequest,
    VoiceReadbackResponse,
    ConfirmationStatus,
    Phase3RecordPayload
)
from backend.ai.rule_extractor import RuleExtractor
from backend.ai.qwen_extractor import QwenExtractor
from backend.ai.voice_readback import VoiceReadbackService
from backend.ai.voice_corrector import VoiceCorrectionHandler
from backend.ai.phase3_client import Phase3Client
from backend.safety.danger_signs import DangerSignDetector
from backend.safety.guidelines import PUBLIC_HEALTH_RULES

logger = logging.getLogger("asha_sahayak.routes.ai")

router = APIRouter(prefix="/api/ai", tags=["AI Understanding & Safety"])

# Service singletons - Primary engine is Python Rule-Based Extractor (Zero Qwen dependency)
danger_detector = DangerSignDetector()
extractor = RuleExtractor(danger_detector=danger_detector)
qwen_extractor = QwenExtractor(danger_detector=danger_detector)
voice_readback_service = VoiceReadbackService()
voice_corrector = VoiceCorrectionHandler(danger_detector=danger_detector)
phase3_client = Phase3Client()


class ProcessTranscriptResponse(BaseModel):
    """Combined response returning extracted record and audio readback."""
    record: FieldExtractionOutput
    voice_readback: VoiceReadbackResponse


class SpeechSynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: str = Field(default="kn-en")


@router.post(
    "/process-transcript",
    response_model=ProcessTranscriptResponse,
    summary="Process transcript from Phase 1 STT",
    description=(
        "Accepts transcript from Phase 1, understands speech across kn, en, kn-en, "
        "extracts clinical fields using Qwen AI, checks predefined danger signs, "
        "and generates Gnani Timbre read-back speech."
    )
)
async def process_transcript(input_data: Phase1TranscriptInput):
    """Entry point for Phase 1 output."""
    if input_data.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot process transcript with Phase 1 status: '{input_data.status}'. Expected 'completed'."
        )

    session_id = input_data.session_id or f"SES-{uuid.uuid4().hex[:8]}"

    # Extract structured fields using Python Rule & Medical Vocabulary Extractor
    record = extractor.extract_structured_record(
        transcript=input_data.transcript,
        language=input_data.language,
        pre_selected_beneficiary_id=input_data.beneficiary_id,
        session_id=session_id
    )

    # Synthesize readback voice with Gnani Timbre
    voice_resp = await voice_readback_service.synthesize_speech(
        text=record.readback_text or "Details extracted. Is this correct?",
        language=input_data.language
    )

    return ProcessTranscriptResponse(
        record=record,
        voice_readback=voice_resp
    )


@router.post(
    "/correct-record",
    response_model=ProcessTranscriptResponse,
    summary="Voice or text correction of specific fields",
    description=(
        "Accepts an ASHA worker's verbal correction (e.g., 'No, weight is 2.8 kilograms.'), "
        "updates ONLY the targeted field, preserves other data, and reads back updated details."
    )
)
async def correct_record(request: CorrectionRequest):
    """Apply field-specific correction without confirming the record."""
    updated_record, summary = voice_corrector.apply_correction(
        correction_transcript=request.correction_transcript,
        current_record=request.current_record,
        language=request.language
    )

    # Re-synthesize voice readback with the updated values
    voice_resp = await voice_readback_service.synthesize_speech(
        text=updated_record.readback_text,
        language=request.language
    )

    return ProcessTranscriptResponse(
        record=updated_record,
        voice_readback=voice_resp
    )


@router.post(
    "/confirm-record",
    summary="Explicit worker confirmation and Phase 3 handoff",
    description=(
        "Requires explicit worker confirmation before finalizing. "
        "Sets status to 'confirmed' and sends common JSON structure to Phase 3."
    )
)
async def confirm_record(request: ConfirmationRequest):
    """Finalizes record upon explicit worker confirmation and sends to Phase 3."""
    if not request.confirmed:
        return {
            "status": "unconfirmed",
            "message": "Record not confirmed by worker. Confirmation remains pending.",
            "record": request.record
        }

    # Set confirmed status
    confirmed_record = request.record
    confirmed_record.confirmation_status = ConfirmationStatus.CONFIRMED

    # Transmit to Phase 3
    phase3_result = await phase3_client.send_confirmed_record(confirmed_record)

    return {
        "status": "confirmed",
        "message": "Record explicitly confirmed by ASHA worker and forwarded to Phase 3.",
        "phase3_handoff": phase3_result,
        "record": confirmed_record
    }


@router.post(
    "/synthesize-speech",
    response_model=VoiceReadbackResponse,
    summary="Gnani Timbre v3.0 voice synthesis",
    description="Synthesize text to speech using Gnani Timbre for Kannada, English, or code-mix."
)
async def synthesize_speech(request: SpeechSynthesisRequest):
    """Direct TTS synthesis utility."""
    return await voice_readback_service.synthesize_speech(
        text=request.text,
        language=request.language
    )


@router.get(
    "/danger-signs/rules",
    summary="Public health danger sign protocols",
    description="Returns all predefined danger-sign rules and public health guideline citations."
)
async def get_danger_sign_rules():
    """List all documented public health rules."""
    rules_data = []
    for code, rule in PUBLIC_HEALTH_RULES.items():
        rules_data.append({
            "code": rule.code,
            "name_en": rule.name_en,
            "name_kn": rule.name_kn,
            "category": rule.category,
            "severity": rule.severity.value,
            "guideline_source": rule.guideline_source,
            "keywords_en": rule.keywords_en,
            "keywords_kn": rule.keywords_kn,
            "referral_instruction_en": rule.referral_instruction_en,
            "referral_instruction_kn": rule.referral_instruction_kn,
        })
    return {
        "total_rules": len(rules_data),
        "guidelines": [
            "MoHFW Home Based Newborn Care (HBNC) Operational Guidelines (Govt of India)",
            "WHO/UNICEF Integrated Management of Neonatal and Childhood Illness (IMNCI)",
            "MoHFW Guidelines for Antenatal Care (ANC) and Skilled Attendance at Birth"
        ],
        "rules": rules_data
    }


@router.get("/health", summary="Phase 2 Health Check")
async def health_check():
    """Verify Phase 2 AI & Safety backend status."""
    return {
        "status": "healthy",
        "phase": 2,
        "module": "AI Understanding, Data Extraction and Safety",
        "engine": "Python Rule-Based & Medical Vocabulary Extraction Engine (Zero Qwen dependency)",
        "qwen_available": bool(qwen_extractor.api_key),
        "gnani_configured": bool(voice_readback_service.api_key or voice_readback_service.token),
        "danger_signs_rules_loaded": len(PUBLIC_HEALTH_RULES),
        "phase3_endpoint": phase3_client.endpoint_url
    }


@router.websocket("/ws/interaction")
async def websocket_interaction(websocket: WebSocket):
    """
    WebSocket endpoint for bidirectional conversational voice interaction.
    Allows ASHA worker client to stream transcripts, corrections, and confirmations.
    """
    await websocket.accept()
    session_id = f"WS-SES-{uuid.uuid4().hex[:8]}"
    current_record: FieldExtractionOutput = None
    language = "kn-en"

    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "ASHA SAHAYAK Phase 2 AI voice agent connected (Rule Engine)."
        })

        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type", "process_transcript")

            if msg_type == "process_transcript":
                transcript = data.get("transcript", "")
                language = data.get("language", language)
                beneficiary_id = data.get("beneficiary_id")

                current_record = extractor.extract_structured_record(
                    transcript=transcript,
                    language=language,
                    pre_selected_beneficiary_id=beneficiary_id,
                    session_id=session_id
                )

                voice_resp = await voice_readback_service.synthesize_speech(
                    text=current_record.readback_text,
                    language=language
                )

                await websocket.send_json({
                    "type": "record_extracted",
                    "record": current_record.model_dump(),
                    "voice_readback": voice_resp.model_dump()
                })

            elif msg_type == "correct":
                correction_text = data.get("correction_transcript", "")
                language = data.get("language", language)

                if not current_record:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No active record in this session to correct."
                    })
                    continue

                current_record, summary = voice_corrector.apply_correction(
                    correction_transcript=correction_text,
                    current_record=current_record,
                    language=language
                )

                voice_resp = await voice_readback_service.synthesize_speech(
                    text=current_record.readback_text,
                    language=language
                )

                await websocket.send_json({
                    "type": "record_corrected",
                    "summary": summary,
                    "record": current_record.model_dump(),
                    "voice_readback": voice_resp.model_dump()
                })

            elif msg_type == "confirm":
                is_confirmed = data.get("confirmed", True)
                if not current_record:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No active record to confirm."
                    })
                    continue

                if is_confirmed:
                    current_record.confirmation_status = ConfirmationStatus.CONFIRMED
                    phase3_res = await phase3_client.send_confirmed_record(current_record)
                    await websocket.send_json({
                        "type": "record_confirmed",
                        "message": "Record confirmed and sent to Phase 3 register.",
                        "record": current_record.model_dump(),
                        "phase3_handoff": phase3_res
                    })
                else:
                    await websocket.send_json({
                        "type": "record_unconfirmed",
                        "message": "Record confirmation declined.",
                        "record": current_record.model_dump()
                    })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected: %s", session_id)
    except Exception as e:
        logger.error("WebSocket interaction error: %s", str(e))
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
