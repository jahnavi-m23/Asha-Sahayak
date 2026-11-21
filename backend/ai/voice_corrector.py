# backend/ai/voice_corrector.py
"""
Voice Correction Handler for ASHA Worker Interaction.
Processes verbal corrections such as:
- "No, weight is 2.8 kilograms."
- "Next visit date is 2026-11-28."
- "Vaccine is BCG not OPV-1."
- "ಸರಿ ಇಲ್ಲ, ತೂಕ 2.8 ಕೆಜಿ" (Not correct, weight is 2.8 kg)

RULES:
- Updates only the relevant field.
- Preserves all other previously extracted fields.
- Re-validates the updated record.
- Recomputes missing fields.
- Never marks the record confirmed until explicit confirmation is voiced.
"""
import re
import copy
from typing import Tuple
from backend.models.schemas import (
    FieldExtractionOutput,
    ConfirmationStatus,
    CorrectionRequest
)
from backend.ai.transcript_parser import TranscriptParser
from backend.safety.danger_signs import DangerSignDetector
from backend.safety.referral_advisor import ReferralAdvisor


class VoiceCorrectionHandler:
    """Manages iterative corrections by the worker."""

    def __init__(self, danger_detector: DangerSignDetector = None):
        self.danger_detector = danger_detector or DangerSignDetector()

    def apply_correction(
        self,
        correction_transcript: str,
        current_record: FieldExtractionOutput,
        language: str = "kn-en"
    ) -> Tuple[FieldExtractionOutput, str]:
        """
        Apply worker's correction to the current record.
        Returns the updated record and an explanation of the change.
        """
        # Create a deep copy of the existing record to maintain immutability
        updated = copy.deepcopy(current_record)
        clean_text = TranscriptParser.normalize_transcript(correction_transcript)
        lower_text = clean_text.lower()
        modified_fields = []

        # 1. Check for WEIGHT correction
        new_weight = TranscriptParser.extract_weight(clean_text)
        if new_weight or "weight" in lower_text or "ತೂಕ" in lower_text:
            if new_weight:
                updated.weight = new_weight
                modified_fields.append("weight")

        # 1b. Check for AGE correction
        new_age = TranscriptParser.extract_age(clean_text)
        if new_age or "age" in lower_text or "ವಯಸ್ಸು" in lower_text:
            if new_age:
                updated.age = new_age
                modified_fields.append("age")

        # 2. Check for VACCINATION correction
        # Handles "Vaccine is BCG not OPV-1" or "BCG vaccine"
        new_vaccines = TranscriptParser.extract_vaccinations(clean_text)
        if new_vaccines:
            updated.vaccinations_due = new_vaccines
            modified_fields.append("vaccinations_due")

        # 3. Check for NEXT VISIT DATE correction
        new_date = TranscriptParser.extract_next_visit_date(clean_text)
        if new_date or "next visit" in lower_text or "ಮುಂದಿನ ಭೇಟಿ" in lower_text:
            if new_date:
                updated.next_visit_date = new_date
                modified_fields.append("next_visit_date")

        # 4. Check for BENEFICIARY ID correction
        new_bid = TranscriptParser.extract_beneficiary_id(clean_text)
        if new_bid:
            updated.beneficiary_id = new_bid
            modified_fields.append("beneficiary_id")

        # 5. Check for VISIT TYPE correction
        if any(term in lower_text for term in ["visit type", "anc", "pnc", "hbnc", "ಗರ್ಭಿಣಿ", "ಬಾಣಂತಿ"]):
            new_type = TranscriptParser.infer_visit_type(clean_text)
            if new_type:
                updated.visit_type = new_type
                modified_fields.append("visit_type")

        # 6. Re-evaluate any danger signs mentioned in the correction
        new_danger_signs = self.danger_detector.detect_danger_signs(clean_text, language=language)
        if new_danger_signs:
            # Merge danger signs without duplicates
            existing_codes = {d.code for d in updated.danger_signs}
            for ds in new_danger_signs:
                if ds.code not in existing_codes:
                    updated.danger_signs.append(ds)
            updated.referral_required = self.danger_detector.has_actionable_danger_signs(updated.danger_signs)

        # 7. Recompute missing fields
        updated.missing_fields = []
        if not updated.beneficiary_id:
            updated.missing_fields.append("beneficiary_id")
        if not updated.visit_type:
            updated.missing_fields.append("visit_type")
        if not updated.weight:
            updated.missing_fields.append("weight")
        if not updated.vaccinations_due:
            updated.missing_fields.append("vaccinations_due")
        if not updated.next_visit_date:
            updated.missing_fields.append("next_visit_date")

        # 8. Confirmation status MUST remain pending or in_review
        updated.confirmation_status = ConfirmationStatus.IN_REVIEW

        # 9. Generate updated readback script
        updated.readback_text = self._build_updated_readback(updated, language, modified_fields)

        summary_msg = f"Updated: {', '.join(modified_fields)}" if modified_fields else "No specific field update identified."
        return updated, summary_msg

    def _build_updated_readback(
        self,
        record: FieldExtractionOutput,
        language: str,
        modified_fields: list
    ) -> str:
        """Build voice read-back string highlighting updated values."""
        parts = []

        if language == "kn":
            parts.append("ವಿವರಗಳನ್ನು ನವೀಕರಿಸಲಾಗಿದೆ.")
            if record.weight:
                parts.append(f"ಮಗುವಿನ ತೂಕ {record.weight}.")
            if record.vaccinations_due:
                parts.append(f"{', '.join(record.vaccinations_due)} ಲಸಿಕೆ ಬಾಕಿ ಇದೆ.")
            if record.next_visit_date:
                parts.append(f"ಮುಂದಿನ ಭೇಟಿ ದಿನಾಂಕ {record.next_visit_date}.")
            parts.append("ಇದು ಸರಿಯೇ?")
        elif language == "en":
            parts.append("Details updated.")
            if record.weight:
                parts.append(f"Baby weight is {record.weight}.")
            if record.vaccinations_due:
                parts.append(f"{', '.join(record.vaccinations_due)} vaccination is due.")
            if record.next_visit_date:
                parts.append(f"Next visit date is {record.next_visit_date}.")
            parts.append("Is this correct now?")
        else:
            # Code-mixed
            parts.append("Details update maadaayithu.")
            if record.weight:
                parts.append(f"Baby weight is {record.weight}.")
            if record.vaccinations_due:
                parts.append(f"{', '.join(record.vaccinations_due)} is due.")
            if record.next_visit_date:
                parts.append(f"Next visit date is {record.next_visit_date}.")
            parts.append("Is this correct?")

        return " ".join(parts)
