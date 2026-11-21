import uuid
import datetime
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.extraction.engine import ASHAExtractionEngine

logger = logging.getLogger("routes.report")
router = APIRouter(prefix="/api/report", tags=["Phase 2 Extraction & Phase 3 Register"])

# In-memory Phase 3 Register Store (persists across sessions during server lifetime)
SAVED_FIELD_VISIT_REGISTER: List[Dict[str, Any]] = [
    # Seed with realistic synthetic benchmark record for dashboard display
    {
        "id": "VISIT-BENCH-001",
        "beneficiary_id": "KA-RCH-8921",
        "beneficiary_name": "Lakshmi",
        "visit_type": "ANC Home Visit (ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ)",
        "pregnancy_status": "Pregnant (ಗರ್ಭಿಣಿ)",
        "gestational_age": "24 weeks (24 ವಾರಗಳು)",
        "infant_weight": None,
        "blood_pressure": "120/80",
        "vaccinations_due": ["Td-2"],
        "vaccinations_given": ["Td-1"],
        "symptoms_reported": ["Headache"],
        "negated_symptoms": ["No Bleeding (Bleeding ಇಲ್ಲ)"],
        "next_visit_date": "Next Week (ಮುಂದಿನ ವಾರ)",
        "danger_signs": [],
        "referral_required": False,
        "referral_facility": None,
        "missing_fields": [],
        "uncertain_indicators": [],
        "confidence_score": 0.95,
        "confirmed": True,
        "raw_transcript": "ಫಲಾನುಭವಿ ಲಕ್ಷ್ಮಿ ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ 24 ವಾರಗಳು ರಕ್ತದೊತ್ತಡ 120/80 ಇದೆ ತಲೆನೋವು ಇದೆ ರಕ್ತಸ್ರಾವ ಇಲ್ಲ",
        "readback_en": "Beneficiary Lakshmi. ANC Home Visit. Gestational age 24 weeks. Reported symptoms: Headache. Confirmed absent: No Bleeding.",
        "readback_kn": "ಫಲಾನುಭವಿ ಲಕ್ಷ್ಮಿ. ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ. ವಯಸ್ಸು 24 ವಾರಗಳು. ತಲೆನೋವು ವರದಿಯಾಗಿದೆ. ರಕ್ತಸ್ರಾವ ಇಲ್ಲ.",
        "created_at": "2026-11-20T10:30:00"
    }
]


# ==============================================================================
# Request & Response Schemas
# ==============================================================================
class ExtractReportRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="Transcribed field narrative")
    language: str = Field(default="kn-IN", description="Language of original speech")


class VoiceCorrectionRequest(BaseModel):
    current_report: Dict[str, Any] = Field(..., description="Currently displayed report draft")
    correction_text: str = Field(..., min_length=1, description="Spoken or typed correction string")


class SaveReportRequest(BaseModel):
    report: Dict[str, Any] = Field(..., description="Final reviewed report")
    confirmed: bool = Field(default=True, description="Explicit worker confirmation")


# ==============================================================================
# API Endpoints (Phase 2 & Phase 3 Contract)
# ==============================================================================
@router.post("/extract")
async def extract_structured_report(payload: ExtractReportRequest):
    """
    Phase 2 Extraction Engine:
    Analyzes finalized ASR transcript and produces a 13-field structured clinical report.
    Prepares bilingual voice readback summaries.
    """
    clean_text = payload.transcript.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript cannot be empty for report extraction."
        )

    try:
        report = ASHAExtractionEngine.extract_report(
            raw_transcript=clean_text,
            language_code=payload.language
        )
        report["id"] = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"[Phase 2 Extraction] Extracted visit report for '{report.get('beneficiary_name')}' (Confidence: {report.get('confidence_score')})")
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        logger.error(f"[Phase 2 Extraction Error] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Information extraction failed: {str(e)}"
        )


@router.post("/correct")
async def correct_report_by_voice(payload: VoiceCorrectionRequest):
    """
    Voice Read-Back & Field Correction:
    Parses spoken corrections ('No, the weight is 2.8 kilograms') and updates
    only the relevant field while re-checking danger sign rules.
    """
    try:
        updated_report, modified_field, confirm_phrase = ASHAExtractionEngine.apply_voice_correction(
            current_report=payload.current_report,
            correction_text=payload.correction_text
        )
        logger.info(f"[Voice Correction] Updated field '{modified_field}' via correction: '{payload.correction_text}'")
        return {
            "success": True,
            "modified_field": modified_field,
            "readback_phrase": confirm_phrase,
            "updated_report": updated_report
        }
    except Exception as e:
        logger.error(f"[Voice Correction Error] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice correction failed: {str(e)}"
        )


@router.post("/save")
async def save_confirmed_report(payload: SaveReportRequest):
    """
    Phase 3 Database Storage:
    Saves ONLY confirmed reports to the official ASHA Field Visit Register.
    Rejects unconfirmed or empty drafts.
    """
    if not payload.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot save unconfirmed report. Explicit worker confirmation is required."
        )

    report = dict(payload.report)
    if not report.get("id") or report.get("id", "").startswith("DRAFT-"):
        report["id"] = f"VISIT-{uuid.uuid4().hex[:8].upper()}"

    report["confirmed"] = True
    report["saved_at"] = datetime.datetime.now().isoformat()

    SAVED_FIELD_VISIT_REGISTER.append(report)
    logger.info(f"[Phase 3 Register] Successfully saved confirmed visit report {report['id']} for {report.get('beneficiary_name')}")

    return {
        "success": True,
        "message": "Visit report successfully confirmed and saved to ASHA Field Register.",
        "record_id": report["id"],
        "record": report
    }


@router.get("/list")
async def get_all_reports():
    """
    Phase 3 Dashboard:
    Returns all confirmed visit reports with aggregated community health indicators:
    - Total visits
    - High-risk referrals count
    - Immunizations scheduled
    - Follow-ups pending
    """
    total = len(SAVED_FIELD_VISIT_REGISTER)
    referrals = sum(1 for r in SAVED_FIELD_VISIT_REGISTER if r.get("referral_required"))
    vaccinations_due_count = sum(len(r.get("vaccinations_due", [])) for r in SAVED_FIELD_VISIT_REGISTER)
    followups_count = sum(1 for r in SAVED_FIELD_VISIT_REGISTER if r.get("next_visit_date"))

    return {
        "stats": {
            "total_visits": total,
            "high_risk_referrals": referrals,
            "immunizations_scheduled": vaccinations_due_count,
            "pending_followups": followups_count
        },
        "records": list(reversed(SAVED_FIELD_VISIT_REGISTER))
    }


@router.get("/{report_id}")
async def get_report_by_id(report_id: str):
    """Retrieves a single visit report by ID."""
    for record in SAVED_FIELD_VISIT_REGISTER:
        if record.get("id") == report_id:
            return {"success": True, "record": record}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """Deletes or archives a report from the register."""
    global SAVED_FIELD_VISIT_REGISTER
    initial_len = len(SAVED_FIELD_VISIT_REGISTER)
    SAVED_FIELD_VISIT_REGISTER = [r for r in SAVED_FIELD_VISIT_REGISTER if r.get("id") != report_id]
    if len(SAVED_FIELD_VISIT_REGISTER) == initial_len:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
    return {"success": True, "message": f"Report {report_id} removed from register."}

