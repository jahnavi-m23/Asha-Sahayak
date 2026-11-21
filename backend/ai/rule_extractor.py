# backend/ai/rule_extractor.py
"""
ASHA SAHAYAK - Python Rule-Based Structured Field Extraction Engine.
Operates completely without external AI APIs (no Qwen dependency).
Features:
- Regex-based weight, age, and date extraction.
- Multilingual medical vocabulary matching (Kannada, English, code-mix).
- Strict zero-hallucination policy (missing fields remain strictly null).
- Ambiguity and uncertainty detection (flags uncertain items rather than guessing).
- Predefined public health danger-sign evaluation (MoHFW HBNC, ANC, IMNCI).
- Pydantic schema validation.
"""
import logging
from typing import Optional, Dict, Any, List
from pydantic import ValidationError

from backend.models.schemas import (
    FieldExtractionOutput,
    ConfirmationStatus,
)
from backend.safety.danger_signs import DangerSignDetector
from backend.safety.referral_advisor import ReferralAdvisor
from backend.ai.transcript_parser import TranscriptParser

logger = logging.getLogger("asha_sahayak.ai.rule_extractor")


class RuleExtractor:
    """Python-based clinical entity extractor for ASHA workers."""

    def __init__(self, danger_detector: Optional[DangerSignDetector] = None):
        self.danger_detector = danger_detector or DangerSignDetector()

    def extract_structured_record(
        self,
        transcript: str,
        language: str = "kn-en",
        pre_selected_beneficiary_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> FieldExtractionOutput:
        """
        Process transcript with rule-based regex and medical dictionaries.
        Guarantees zero hallucination and immediate deterministic execution.
        """
        cleaned_transcript = TranscriptParser.normalize_transcript(transcript)

        # 1. Rule-based danger sign detection (MoHFW / IMNCI public health protocols)
        detected_danger_signs = self.danger_detector.detect_danger_signs(
            cleaned_transcript,
            language=language
        )
        referral_required = self.danger_detector.has_actionable_danger_signs(detected_danger_signs)

        # 2. Extract clinical entities using Python regex and vocabulary dictionaries
        beneficiary_id = TranscriptParser.extract_beneficiary_id(cleaned_transcript)
        if not beneficiary_id and pre_selected_beneficiary_id:
            beneficiary_id = pre_selected_beneficiary_id

        weight = TranscriptParser.extract_weight(cleaned_transcript)
        age = TranscriptParser.extract_age(cleaned_transcript)
        vaccines = TranscriptParser.extract_vaccinations(cleaned_transcript)
        next_visit = TranscriptParser.extract_next_visit_date(cleaned_transcript)
        visit_type = TranscriptParser.infer_visit_type(cleaned_transcript)

        # 3. Detect ambiguity and uncertainty rather than guessing
        has_ambiguity, uncertain_flags = TranscriptParser.detect_ambiguity_and_uncertainty(cleaned_transcript)

        raw_fields: Dict[str, Any] = {
            "beneficiary_id": beneficiary_id,
            "visit_type": visit_type,
            "weight": weight,
            "age": age,
            "vaccinations_due": vaccines,
            "next_visit_date": next_visit,
            "uncertain_fields": uncertain_flags,
            "danger_signs": detected_danger_signs,
            "referral_required": referral_required,
            "confirmation_status": ConfirmationStatus.PENDING,
            "session_id": session_id,
        }

        # 4. Compute missing mandatory/recommended fields (Strictly null when absent)
        missing_fields = self._compute_missing_fields(raw_fields)
        raw_fields["missing_fields"] = missing_fields

        # 5. Generate targeted clarification questions for the worker
        raw_fields["clarification_prompt"] = self._generate_clarification_prompt(missing_fields, language)

        # 6. Generate voice readback script for Gnani Timbre
        raw_fields["readback_text"] = self._generate_readback_text(
            raw_fields, language, detected_danger_signs, uncertain_flags
        )

        # 7. Validate output against Pydantic model
        try:
            return FieldExtractionOutput.model_validate(raw_fields)
        except ValidationError as val_err:
            logger.error("Rule extraction schema validation error: %s", str(val_err))
            return FieldExtractionOutput(
                beneficiary_id=beneficiary_id,
                visit_type=visit_type or "Newborn home visit",
                weight=None,
                vaccinations_due=[],
                next_visit_date=None,
                missing_fields=["weight", "vaccinations_due", "next_visit_date"],
                danger_signs=detected_danger_signs,
                referral_required=referral_required,
                confirmation_status=ConfirmationStatus.PENDING,
                clarification_prompt="Details unclear. Please repeat the information.",
                readback_text="Details unclear. Please repeat the information.",
                session_id=session_id
            )

    def _compute_missing_fields(self, fields: Dict[str, Any]) -> List[str]:
        """Compute list of missing expected fields."""
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
        """Generate targeted clarification question in worker's language."""
        if not missing_fields:
            return None

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
        danger_signs: List[Any],
        uncertain_flags: List[str]
    ) -> str:
        """Build localized readback string for Gnani Timbre."""
        parts = []

        # 1. Urgent referral message if actionable danger signs exist
        active_danger_signs = [
            d for d in danger_signs
            if not getattr(d, 'is_negated', False) and not getattr(d, 'is_uncertain', False)
        ]
        if active_danger_signs:
            ref_msg = ReferralAdvisor.generate_referral_summary(danger_signs, language)
            if ref_msg:
                parts.append(ref_msg)

        # 2. Ambiguity / uncertainty caution
        if uncertain_flags:
            if language == "kn":
                parts.append("ಗಮನಿಸಿ: ಕೆಲವು ಮಾಹಿತಿಗಳು ಅಸ್ಪಷ್ಟವಾಗಿವೆ.")
            else:
                parts.append("Note: Some information was unclear and needs verification.")

        # 3. Readback of extracted fields
        weight = fields.get("weight")
        age = fields.get("age")
        vaccines = fields.get("vaccinations_due") or []
        next_visit = fields.get("next_visit_date")

        if language == "kn":
            if age:
                parts.append(f"ಮಗುವಿನ ವಯಸ್ಸು {age}.")
            if weight:
                parts.append(f"ಮಗುವಿನ ತೂಕ {weight}.")
            if vaccines:
                vaccine_str = ", ".join(vaccines)
                parts.append(f"{vaccine_str} ಲಸಿಕೆ ಬಾಕಿ ಇದೆ.")
            if next_visit:
                parts.append(f"ಮುಂದಿನ ಭೇಟಿ ದಿನಾಂಕ {next_visit}.")
            parts.append("ಇದು ಸರಿಯೇ?")
        elif language == "en":
            if age:
                parts.append(f"Baby age is {age}.")
            if weight:
                parts.append(f"Baby weight is {weight}.")
            if vaccines:
                vaccine_str = ", ".join(vaccines)
                parts.append(f"{vaccine_str} vaccination is due.")
            if next_visit:
                parts.append(f"Next visit date is {next_visit}.")
            parts.append("Is this correct?")
        else:
            # Code-mixed (kn-en)
            if age:
                parts.append(f"Baby age {age}.")
            if weight:
                parts.append(f"Baby weight is {weight}.")
            if vaccines:
                vaccine_str = ", ".join(vaccines)
                parts.append(f"{vaccine_str} vaccination is due.")
            if next_visit:
                parts.append(f"Next visit date is {next_visit}.")
            parts.append("Is this correct?")

        return " ".join(parts)
