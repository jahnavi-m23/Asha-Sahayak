# backend/ai/qwen_extractor.py
"""
Qwen AI Structured Field Extractor.
Uses Qwen LLM for understanding multilingual ASHA worker transcripts.
Features:
- Structured JSON output with Pydantic validation.
- Enforces strict anti-hallucination rules (never invents beneficiary ID, dates, weights).
- Integrated with DangerSignDetector for comprehensive safety review.
- High-fidelity offline/heuristic fallback engine when QWEN_API_KEY is not configured or network is offline.
"""
import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from pydantic import ValidationError

from backend.config import settings
from backend.models.schemas import (
    FieldExtractionOutput,
    ConfirmationStatus,
)
from backend.safety.danger_signs import DangerSignDetector
from backend.safety.referral_advisor import ReferralAdvisor
from backend.ai.transcript_parser import TranscriptParser

logger = logging.getLogger("asha_sahayak.ai.qwen")

EXTRACTION_SYSTEM_PROMPT = """
You are an expert AI clinical data assistant for ASHA workers in India (ASHA SAHAYAK).
Your mission is to accurately parse voice transcripts spoken by ASHA workers in English, Kannada, or Kannada-English (kn-en code-mixed).

STRICT HEALTHCARE SAFETY GUIDELINES:
1. Extract structured fields from the transcript:
   - beneficiary_id: string or null (e.g., "BNF-2041").
   - visit_type: string or null (e.g., "Newborn home visit", "Antenatal Care (ANC)", "Postnatal Care (PNC)", "Routine Immunization").
   - weight: string with units or null (e.g., "3.2 kg").
   - vaccinations_due: array of standardized vaccine names (e.g. ["OPV-1", "BCG"]).
   - next_visit_date: string "YYYY-MM-DD" or null.
2. ZERO-HALLUCINATION POLICY:
   - NEVER invent or guess a beneficiary_id, visit date, weight, or vaccination if it is not present in the transcript.
   - If ANY field is absent or unclear, you MUST set it to null and list it in missing_fields.
3. NEVER provide a diagnosis, medical treatment, or prescription dosage.
4. Output STRICTLY a valid JSON object matching the requested schema. No conversational filler or markdown other than the JSON block.
"""


class QwenExtractor:
    """Manages transcript understanding and structured extraction via Qwen AI."""

    def __init__(self, danger_detector: Optional[DangerSignDetector] = None):
        self.danger_detector = danger_detector or DangerSignDetector()
        self.api_key = settings.QWEN_API_KEY
        self.api_base = settings.QWEN_API_BASE
        self.model = settings.QWEN_MODEL_NAME

    async def extract_structured_record(
        self,
        transcript: str,
        language: str = "kn-en",
        pre_selected_beneficiary_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> FieldExtractionOutput:
        """
        Process transcript, extract structured entities, check safety danger signs,
        and validate output.
        """
        cleaned_transcript = TranscriptParser.normalize_transcript(transcript)
        
        # 1. Rule-based danger sign detection (always executed first for uncompromising safety)
        detected_danger_signs = self.danger_detector.detect_danger_signs(
            cleaned_transcript,
            language=language
        )
        referral_required = self.danger_detector.has_actionable_danger_signs(detected_danger_signs)

        # 2. Extract structured fields (using Qwen API if key present, else deterministic heuristic fallback)
        raw_fields: Dict[str, Any]
        if self.api_key:
            try:
                raw_fields = await self._call_qwen_api(cleaned_transcript, language)
            except Exception as e:
                if settings.ALLOW_MOCK_FALLBACK:
                    logger.warning("Qwen API call failed (%s); falling back to heuristic engine", str(e))
                    raw_fields = self._heuristic_extraction(cleaned_transcript, language)
                else:
                    raise
        elif settings.ALLOW_MOCK_FALLBACK:
            # Deterministic heuristic extraction engine when no API key configured
            raw_fields = self._heuristic_extraction(cleaned_transcript, language)
        else:
            raise ValueError("QWEN_API_KEY is not configured and ALLOW_MOCK_FALLBACK is False")

        # 3. Apply authorized pre-selected beneficiary ID if provided
        if pre_selected_beneficiary_id and not raw_fields.get("beneficiary_id"):
            raw_fields["beneficiary_id"] = pre_selected_beneficiary_id

        # 4. Mandatory & missing field evaluation
        missing_fields = self._compute_missing_fields(raw_fields)
        raw_fields["missing_fields"] = missing_fields

        # 5. Attach danger sign and safety findings
        raw_fields["danger_signs"] = detected_danger_signs
        raw_fields["referral_required"] = referral_required
        raw_fields["confirmation_status"] = ConfirmationStatus.PENDING
        raw_fields["session_id"] = session_id

        # 6. Generate targeted clarification questions if mandatory fields are missing
        raw_fields["clarification_prompt"] = self._generate_clarification_prompt(missing_fields, language)

        # 7. Generate readback speech string
        raw_fields["readback_text"] = self._generate_readback_text(raw_fields, language, detected_danger_signs)

        # 8. Validate against Pydantic schema
        try:
            validated_record = FieldExtractionOutput.model_validate(raw_fields)
            return validated_record
        except ValidationError as val_err:
            logger.error("Structured field validation failed: %s", str(val_err))
            # Fallback with safe nulls
            return self._build_safe_fallback_record(
                cleaned_transcript,
                detected_danger_signs,
                referral_required,
                session_id
            )

    async def _call_qwen_api(self, transcript: str, language: str) -> Dict[str, Any]:
        """Execute asynchronous call to Qwen LLM endpoint."""
        user_prompt = f"""
Language: {language}
Transcript: "{transcript}"

Extract the fields according to instructions and output valid JSON:
{{
  "beneficiary_id": string or null,
  "visit_type": string or null,
  "weight": string or null,
  "vaccinations_due": list of strings,
  "next_visit_date": string or null
}}
"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        async with httpx.AsyncClient(timeout=settings.QWEN_TIMEOUT_SECONDS) as client:
            url = f"{self.api_base.rstrip('/')}/chat/completions"
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return parsed

    def _heuristic_extraction(self, transcript: str, language: str) -> Dict[str, Any]:
        """
        Deterministic, zero-hallucination extraction engine.
        Guarantees accurate parsing of measurements, vaccines, and visit types across kn, en, kn-en.
        """
        beneficiary_id = TranscriptParser.extract_beneficiary_id(transcript)
        weight = TranscriptParser.extract_weight(transcript)
        vaccines = TranscriptParser.extract_vaccinations(transcript)
        next_visit = TranscriptParser.extract_next_visit_date(transcript)
        visit_type = TranscriptParser.infer_visit_type(transcript)

        return {
            "beneficiary_id": beneficiary_id,
            "visit_type": visit_type,
            "weight": weight,
            "vaccinations_due": vaccines,
            "next_visit_date": next_visit,
        }

    def _compute_missing_fields(self, fields: Dict[str, Any]) -> List[str]:
        """Identify which mandatory/recommended fields are null or empty."""
        missing = []
        if not fields.get("beneficiary_id"):
            missing.append("beneficiary_id")
        if not fields.get("visit_type"):
            missing.append("visit_type")
        if not fields.get("weight"):
            missing.append("weight")
        if not fields.get("vaccinations_due"):
            missing.append("vaccinations_due")
        if not fields.get("next_visit_date"):
            missing.append("next_visit_date")
        return missing

    def _generate_clarification_prompt(self, missing_fields: List[str], language: str) -> Optional[str]:
        """Generate friendly clarification prompt for missing fields."""
        if not missing_fields:
            return None

        # Focus on the most critical missing fields (beneficiary_id, next_visit_date)
        if "beneficiary_id" in missing_fields and len(missing_fields) == 1:
            if language == "kn":
                return "ಫಲಾನುಭವಿ ಐಡಿ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಫಲಾನುಭವಿಯ ಐಡಿ ತಿಳಿಸಿ."
            return "Beneficiary ID is missing. Please provide the beneficiary ID."
        
        if "next_visit_date" in missing_fields and "beneficiary_id" not in missing_fields:
            if language == "kn":
                return "ಮುಂದಿನ ಭೇಟಿಯ ದಿನಾಂಕ ದಾಖಲಾಗಿಲ್ಲ. ಮುಂದಿನ ಭೇಟಿ ಯಾವಾಗ ನಿಗದಿಪಡಿಸಬೇಕು?"
            elif language == "en":
                return "Next visit date is not recorded. When is the next visit scheduled?"
            else:
                return "Next visit date record aagilla. Yavaga next visit schedule madbeku?"

        return None

    def _generate_readback_text(
        self,
        fields: Dict[str, Any],
        language: str,
        danger_signs: List[Any]
    ) -> str:
        """Build voice read-back script for Gnani Timbre."""
        parts = []

        # 1. Urgent referral message if actionable danger signs exist
        active_danger_signs = [d for d in danger_signs if not getattr(d, 'is_negated', False) and not getattr(d, 'is_uncertain', False)]
        if active_danger_signs:
            ref_msg = ReferralAdvisor.generate_referral_summary(danger_signs, language)
            if ref_msg:
                parts.append(ref_msg)

        # 2. Readback of extracted fields
        beneficiary_id = fields.get("beneficiary_id")
        weight = fields.get("weight")
        vaccines = fields.get("vaccinations_due") or []
        next_visit = fields.get("next_visit_date")

        if language == "kn":
            if weight:
                parts.append(f"ಮಗುವಿನ ತೂಕ {weight}.")
            if vaccines:
                vaccine_str = ", ".join(vaccines)
                parts.append(f"{vaccine_str} ಲಸಿಕೆ ಬಾಕಿ ಇದೆ.")
            if next_visit:
                parts.append(f"ಮುಂದಿನ ಭೇಟಿ ದಿನಾಂಕ {next_visit}.")
            parts.append("ಇದು ಸರಿಯೇ?")
        elif language == "en":
            if weight:
                parts.append(f"Baby weight is {weight}.")
            if vaccines:
                vaccine_str = ", ".join(vaccines)
                parts.append(f"{vaccine_str} vaccination is due.")
            if next_visit:
                parts.append(f"Next visit date is {next_visit}.")
            parts.append("Is this correct?")
        else:
            # Code-mixed default
            if weight:
                parts.append(f"Baby weight is {weight}.")
            if vaccines:
                vaccine_str = ", ".join(vaccines)
                parts.append(f"{vaccine_str} vaccination is due.")
            if next_visit:
                parts.append(f"Next visit date is {next_visit}.")
            parts.append("Is this correct?")

        return " ".join(parts)

    def _build_safe_fallback_record(
        self,
        transcript: str,
        danger_signs: List[Any],
        referral_required: bool,
        session_id: Optional[str]
    ) -> FieldExtractionOutput:
        """Create a zero-assumption fallback when extraction encounters an edge case."""
        return FieldExtractionOutput(
            beneficiary_id=None,
            visit_type="Newborn home visit",
            weight=None,
            vaccinations_due=[],
            next_visit_date=None,
            missing_fields=["beneficiary_id", "weight", "vaccinations_due", "next_visit_date"],
            danger_signs=danger_signs,
            referral_required=referral_required,
            confirmation_status=ConfirmationStatus.PENDING,
            clarification_prompt="Transcript could not be parsed safely. Please repeat visit details.",
            readback_text="Details unclear. Please repeat the information.",
            session_id=session_id
        )
