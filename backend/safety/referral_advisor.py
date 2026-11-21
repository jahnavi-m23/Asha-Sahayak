# backend/safety/referral_advisor.py
"""
Referral Advisor module.
Generates standardized, actionable referral instructions for ASHA workers.

CRITICAL PUBLIC HEALTH ETHICS & SAFETY:
- Never provide clinical diagnosis.
- Never prescribe medication or treatment.
- Never specify medication dosages.
- Direct patients immediately to authorized public health facilities (PHC, CHC, FRU, District Hospital).
"""
from typing import List, Optional
from backend.models.schemas import DangerSignDetection, DangerSignSeverity


class ReferralAdvisor:
    """Generates localized referral instructions for detected danger signs."""

    @staticmethod
    def generate_referral_summary(
        danger_signs: List[DangerSignDetection],
        language: str = "kn-en"
    ) -> Optional[str]:
        """
        Generate a clear, urgency-prioritized voice and text instruction for the ASHA worker.
        Avoids all medical prescribing; focuses entirely on immediate referral action.
        """
        active_signs = [d for d in danger_signs if not d.is_negated and not d.is_uncertain]
        uncertain_signs = [d for d in danger_signs if not d.is_negated and d.is_uncertain]

        if not active_signs and not uncertain_signs:
            return None

        # Determine highest severity
        has_critical = any(d.severity == DangerSignSeverity.CRITICAL_EMERGENCY for d in active_signs)
        
        # Build language-specific messaging
        if language == "kn":
            return ReferralAdvisor._build_kannada_referral(active_signs, uncertain_signs, has_critical)
        elif language == "en":
            return ReferralAdvisor._build_english_referral(active_signs, uncertain_signs, has_critical)
        else:
            # Code-mixed (kn-en)
            return ReferralAdvisor._build_code_mixed_referral(active_signs, uncertain_signs, has_critical)

    @staticmethod
    def _build_english_referral(
        active: List[DangerSignDetection],
        uncertain: List[DangerSignDetection],
        has_critical: bool
    ) -> str:
        parts = []
        if has_critical:
            parts.append("EMERGENCY DANGER SIGN DETECTED.")
            for ds in active:
                parts.append(f"- {ds.name}: {ds.referral_instruction_en}")
            parts.append("Refer immediately to the nearest First Referral Unit (FRU) or Primary Health Centre (PHC). Do not delay.")
        elif active:
            parts.append("URGENT HEALTH WARNING:")
            for ds in active:
                parts.append(f"- {ds.name}: {ds.referral_instruction_en}")
            parts.append("Arrange referral to the nearest Primary Health Centre (PHC) for prompt clinical evaluation.")

        if uncertain:
            parts.append("NOTE FOR HUMAN REVIEW:")
            for ds in uncertain:
                parts.append(f"- Possible sign '{ds.name}' mentioned with uncertainty. Verify symptoms in person.")

        return " ".join(parts)

    @staticmethod
    def _build_kannada_referral(
        active: List[DangerSignDetection],
        uncertain: List[DangerSignDetection],
        has_critical: bool
    ) -> str:
        parts = []
        if has_critical:
            parts.append("ತುರ್ತು ಅಪಾಯದ ಲಕ್ಷಣ ಕಂಡುಬಂದಿದೆ!")
            for ds in active:
                kn_name = ds.name_kannada or ds.name
                parts.append(f"- {kn_name}: {ds.referral_instruction_kn}")
            parts.append("ವಿಳಂಬ ಮಾಡದೆ ತಕ್ಷಣ ಹತ್ತಿರದ FRU ಅಥವಾ PHC ಆಸ್ಪತ್ರೆಗೆ ರವಾನಿಸಿ.")
        elif active:
            parts.append("ಆರೋಗ್ಯ ಎಚ್ಚರಿಕೆ:")
            for ds in active:
                kn_name = ds.name_kannada or ds.name
                parts.append(f"- {kn_name}: {ds.referral_instruction_kn}")
            parts.append("ತಕ್ಷಣವೇ ಪ್ರಾಥಮಿಕ ಆರೋಗ್ಯ ಕೇಂದ್ರಕ್ಕೆ (PHC) ಕರೆದೊಯ್ಯಿರಿ.")

        if uncertain:
            parts.append("ಪರಿಶೀಲನೆ ಅಗತ್ಯವಿದೆ:")
            for ds in uncertain:
                kn_name = ds.name_kannada or ds.name
                parts.append(f"- '{kn_name}' ಬಗ್ಗೆ ಸಂದೇಹವಿದೆ. ದಯವಿಟ್ಟು ಸ್ವತಃ ಪರಿಶೀಲಿಸಿ.")

        return " ".join(parts)

    @staticmethod
    def _build_code_mixed_referral(
        active: List[DangerSignDetection],
        uncertain: List[DangerSignDetection],
        has_critical: bool
    ) -> str:
        parts = []
        if has_critical:
            parts.append("URGENT: Critical danger sign detect aagide!")
            for ds in active:
                parts.append(f"{ds.name}: {ds.referral_instruction_en}")
            parts.append("Immediately nearest PHC athava FRU ge refer maadi. Delay madbedi.")
        elif active:
            parts.append("HEALTH ALERT: Danger sign detect aagide.")
            for ds in active:
                parts.append(f"{ds.name}: {ds.referral_instruction_en}")
            parts.append("Checkup ge PHC ge refer maadi.")

        if uncertain:
            for ds in uncertain:
                parts.append(f"Uncertain symptom: '{ds.name}'. Verify in person.")

        return " ".join(parts)
