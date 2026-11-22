"""
ASHA Sahayak - Phase 2 Clinical Information Extraction & Report Engine.
Extracts structured ASHA visit reports from transcribed Kannada, English,
and Kannada-English code-mixed field narratives.

Follows Government of India RCH / NHM and Karnataka Mother & Child Health protocols.
Does not depend on external LLMs (rule-based NLP extraction).
Preserves medical intent, respects negations, identifies clinical red flags,
and supports voice read-back and voice-driven field corrections.
"""

import re
import datetime
from typing import Dict, Any, List, Optional, Tuple

# Predefined Common ASHA Names in Karnataka & Pan-India
COMMON_FEMALE_NAMES = [
    "Lakshmi", "Radhika", "Savitha", "Sunitha", "Meenakshi", "Shilpa", "Pooja",
    "Anitha", "Shanti", "Roopa", "Geetha", "Deepa", "Bhavani", "Suma", "Sushma",
    "Kavitha", "Rekha", "Ashwini", "Vidya", "Manjula", "Prema", "Kusuma", "Parvati",
    "Mary", "Fatima", "Shweta", "Rani", "Pushpa", "Saraswathi", "Gowramma", "Nagaveni"
]

KANNADA_NAMES_MAP = {
    "ಲಕ್ಷ್ಮಿ": "Lakshmi", "ರಾಧಿಕಾ": "Radhika", "ಸವಿತಾ": "Savitha", "ಸುನಿತಾ": "Sunitha",
    "ಮೀನಾಕ್ಷಿ": "Meenakshi", "ಶಿಲ್ಪಾ": "Shilpa", "ಪೂಜಾ": "Pooja", "ಅನಿತಾ": "Anitha",
    "ಶಾಂತಿ": "Shanti", "ರೂಪಾ": "Roopa", "ಗೀತಾ": "Geetha", "ದೀಪಾ": "Deepa",
    "ಭವಾನಿ": "Bhavani", "ಸುಮಾ": "Suma", "ಸುಷ್ಮಾ": "Sushma", "ಕವಿತಾ": "Kavitha",
    "ರೇಖಾ": "Rekha", "ಅಶ್ವಿನಿ": "Ashwini", "ವಿದ್ಯಾ": "Vidya", "ಮಂಜುಳಾ": "Manjula",
    "ಪ್ರೇಮಾ": "Prema", "ಕುಸುಮಾ": "Kusuma", "ಪಾರ್ವತಿ": "Parvati", "ರಾಣಿ": "Rani",
    "ಪುಷ್ಪಾ": "Pushpa", "ಸರಸ್ವತಿ": "Saraswathi", "ಗೌರಮ್ಮ": "Gowramma", "ನಾಗವೇಣಿ": "Nagaveni"
}

# Recognized Vaccines
VACCINE_CATALOG = [
    ("BCG", [r"\bbcg\b", r"ಬಿಸಿಜಿ"]),
    ("OPV-0", [r"\bopv[\s\-]*0\b", r"\bopv[\s\-]*zero\b", r"ಒಪಿವಿ[\s\-]*0"]),
    ("OPV-1", [r"\bopv[\s\-]*1\b", r"\bopv[\s\-]*one\b", r"ಒಪಿವಿ[\s\-]*1"]),
    ("OPV-2", [r"\bopv[\s\-]*2\b", r"\bopv[\s\-]*two\b", r"ಒಪಿವಿ[\s\-]*2"]),
    ("OPV-3", [r"\bopv[\s\-]*3\b", r"\bopv[\s\-]*three\b", r"ಒಪಿವಿ[\s\-]*3"]),
    ("Pentavalent-1", [r"\bpenta(?:valent)?[\s\-]*1\b", r"ಪೆಂಟಾ(?:ವಲೆಂಟ್)?[\s\-]*1"]),
    ("Pentavalent-2", [r"\bpenta(?:valent)?[\s\-]*2\b", r"ಪೆಂಟಾ(?:ವಲೆಂಟ್)?[\s\-]*2"]),
    ("Pentavalent-3", [r"\bpenta(?:valent)?[\s\-]*3\b", r"ಪೆಂಟಾ(?:ವಲೆಂಟ್)?[\s\-]*3"]),
    ("Rotavirus-1", [r"\brota(?:virus)?[\s\-]*1\b", r"ರೋಟಾ(?:ವೈರಸ್)?[\s\-]*1"]),
    ("Rotavirus-2", [r"\brota(?:virus)?[\s\-]*2\b", r"ರೋಟಾ(?:ವೈರಸ್)?[\s\-]*2"]),
    ("Rotavirus-3", [r"\brota(?:virus)?[\s\-]*3\b", r"ರೋಟಾ(?:ವೈರಸ್)?[\s\-]*3"]),
    ("fIPV-1", [r"\bf?ipv[\s\-]*1\b", r"ಐಪಿವಿ[\s\-]*1"]),
    ("fIPV-2", [r"\bf?ipv[\s\-]*2\b", r"ಐಪಿವಿ[\s\-]*2"]),
    ("PCV-1", [r"\bpcv[\s\-]*1\b", r"ಪಿಸಿವಿ[\s\-]*1"]),
    ("PCV-2", [r"\bpcv[\s\-]*2\b", r"ಪಿಸಿವಿ[\s\-]*2"]),
    ("PCV Booster", [r"\bpcv[\s\-]*booster\b", r"ಪಿಸಿವಿ[\s\-]*ಬೂಸ್ಟರ್"]),
    ("MR-1", [r"\bmr[\s\-]*1\b", r"\bmeasles[\s\-]*1\b", r"ಎಂಆರ್[\s\-]*1", r"ದಡಾರ[\s\-]*1"]),
    ("MR-2", [r"\bmr[\s\-]*2\b", r"\bmeasles[\s\-]*2\b", r"ಎಂಆರ್[\s\-]*2", r"ದಡಾರ[\s\-]*2"]),
    ("DPT Booster", [r"\bdpt[\s\-]*booster\b", r"\bdpt\b", r"ಡಿಪಿಟಿ[\s\-]*ಬೂಸ್ಟರ್", r"ಡಿಪಿಟಿ"]),
    ("Td-1", [r"\bt[dt][\s\-]*1\b", r"ಟಿ[ಡಿಟಿ][\s\-]*1"]),
    ("Td-2", [r"\bt[dt][\s\-]*2\b", r"ಟಿ[ಡಿಟಿ][\s\-]*2"]),
    ("Vitamin A", [r"\bvitamin[\s\-]*a\b", r"ವಿಟಮಿನ್[\s\-]*ಎ"]),
]

# Standard Clinical Symptoms Catalog with Kannada Synonyms
SYMPTOMS_CATALOG = [
    ("Fever", [r"\bfever\b", r"ಜ್ವರ", r"temperature", r"ಮೈ ಬಿಸಿ"]),
    ("Cough", [r"\bcough\b", r"ಕೆಮ್ಮು"]),
    ("Cold", [r"\bcold\b", r"ಶೀತ", r"ನೆಗಡಿ"]),
    ("Vomiting", [r"\bvomiting\b", r"\bvomit\b", r"ವಾಂತಿ"]),
    ("Diarrhea", [r"\bdiarrhea\b", r"\bloose motions?\b", r"ಭೇದಿ", r"ಬೇಧಿ", r"ಹೊಟ್ಟೆ ಕೆಡುವುದು"]),
    ("Severe Headache", [r"\bsevere headache\b", r"\bheadache\b", r"ತೀವ್ರ ತಲೆನೋವು", r"ತಲೆನೋವು"]),
    ("Edema / Swelling", [r"\bedema\b", r"\bswelling\b", r"\bswollen feet\b", r"ಊತ", r"ಕಾಲು ಊತ"]),
    ("Abdominal Pain", [r"\babdominal pain\b", r"\bstomach pain\b", r"ಹೊಟ್ಟೆನೋವು", r"ಹೊಟ್ಟೆ ನೋವು"]),
    ("Bleeding", [r"\bbleeding\b", r"\bhemorrhage\b", r"ರಕ್ತಸ್ರಾವ", r"ರಕ್ತ ಹೋಗುವುದು"]),
    ("Water Broke / Fluid Leak", [r"\bwater broke\b", r"\bleaking fluid\b", r"\bwatery discharge\b", r"ನೀರು ಒಡೆದಿದೆ", r"ನೀರು ಹೋಗುತ್ತಿದೆ"]),
    ("Convulsions / Fits", [r"\bconvulsions?\b", r"\bfits\b", r"\bseizures?\b", r"ಫಿಟ್ಸ್", r"ಮೂರ್ಛೆ"]),
    ("Fetal Movement Decreased", [r"\bfetal movement decreased\b", r"\bno movement\b", r"\bless movement\b", r"ಮಗುವಿನ ಚಲನೆ ಕಡಿಮೆ", r"ಚಲನೆ ಇಲ್ಲ"]),
    ("Inability to Feed", [r"\bunable to feed\b", r"\bnot suckling\b", r"\brefusing feed\b", r"ಹಾಲು ಕುಡಿಯುತ್ತಿಲ್ಲ", r"ಹಾಲು ಬಿಟ್ಟಿದೆ"]),
    ("Hypothermia / Cold to touch", [r"\bhypothermia\b", r"\bcold body\b", r"ಮಗು ತಣ್ಣಗಾಗಿದೆ", r"ಶೀತ ದೇಹ"]),
    ("Jaundice", [r"\bjaundice\b", r"\byellow skin\b", r"ಕಾಮಾಲೆ", r"ಹಳದಿ ಚರ್ಮ"]),
]

# Danger Signs Public Health Definitions
DANGER_SIGN_RULES = [
    {
        "id": "MAT_BLEEDING",
        "name": "Maternal Bleeding / Hemorrhage",
        "kannada": "ರಕ್ತಸ್ರಾವ (ರಕ್ತ ಹೋಗುವುದು)",
        "patterns": [r"\bbleeding\b", r"\bhemorrhage\b", r"ರಕ್ತಸ್ರಾವ", r"ರಕ್ತ ಹೋಗುವುದು"],
        "category": "Maternal",
        "severity": "CRITICAL",
        "action": "Immediate emergency transfer to FRU / District Hospital"
    },
    {
        "id": "WATER_BROKE",
        "name": "Premature Rupture of Membranes (Water Broke)",
        "kannada": "ನೀರು ಒಡೆದಿದೆ (ಅಮ್ನಿಯೋಟಿಕ್ ದ್ರವ ಸೋರಿಕೆ)",
        "patterns": [r"\bwater broke\b", r"\bleaking fluid\b", r"ನೀರು ಒಡೆದಿದೆ", r"ನೀರು ಹೋಗುತ್ತಿದೆ"],
        "category": "Maternal",
        "severity": "CRITICAL",
        "action": "Urgent transfer to 24/7 Delivery Facility"
    },
    {
        "id": "CONVULSIONS",
        "name": "Eclampsia / Convulsions / Fits",
        "kannada": "ಫಿಟ್ಸ್ / ಮೂರ್ಛೆ ರೋಗ",
        "patterns": [r"\bconvulsions?\b", r"\bfits\b", r"\bseizures?\b", r"ಫಿಟ್ಸ್", r"ಮೂರ್ಛೆ"],
        "category": "Maternal/Neonatal",
        "severity": "CRITICAL",
        "action": "Immediate administration of MgSO4 at PHC and emergency referral"
    },
    {
        "id": "HIGH_BP",
        "name": "Severe Hypertension / Preeclampsia (BP >= 140/90)",
        "kannada": "ಅಧಿಕ ರಕ್ತದೊತ್ತಡ (BP >= 140/90)",
        "patterns": [r"\b1[4-9]\d[/\s][9]\d\b", r"\b[2]\d\d[/\s]\d{2,3}\b"],
        "category": "Maternal",
        "severity": "HIGH",
        "action": "Refer to Medical Officer at PHC within 24 hours"
    },
    {
        "id": "FETAL_DISTRESS",
        "name": "Decreased / Absent Fetal Movements",
        "kannada": "ಗರ್ಭದಲ್ಲಿ ಮಗುವಿನ ಚಲನೆ ಕಡಿಮೆಯಾಗಿದೆ",
        "patterns": [r"\bfetal movement decreased\b", r"\bno movement\b", r"\bless movement\b", r"ಮಗುವಿನ ಚಲನೆ ಕಡಿಮೆ", r"ಚಲನೆ ಇಲ್ಲ"],
        "category": "Maternal",
        "severity": "HIGH",
        "action": "Immediate NST / Ultrasound evaluation at CHC/Hospital"
    },
    {
        "id": "SEVERE_HEADACHE_VISION",
        "name": "Severe Headache with Visual Disturbance",
        "kannada": "ತೀವ್ರ ತಲೆನೋವು / ದೃಷ್ಟಿ ಮಂಜಾಗುವುದು",
        "patterns": [r"\bsevere headache\b", r"ತೀವ್ರ ತಲೆನೋವು", r"ದೃಷ್ಟಿ ಮಂಜು"],
        "category": "Maternal",
        "severity": "HIGH",
        "action": "Urgent BP evaluation for impending eclampsia"
    },
    {
        "id": "VERY_LOW_BIRTH_WEIGHT",
        "name": "Very Low Birth Weight / Severe Malnutrition (< 2.0 kg)",
        "kannada": "ತೀವ್ರ ಕಡಿಮೆ ಜನನ ತೂಕ (< 2.0 kg)",
        "patterns": [r"\b[0-1]\.\d+\s*(?:kg|ಕೆಜಿ)\b"],
        "category": "Neonatal",
        "severity": "CRITICAL",
        "action": "Admit to SNCU (Special Newborn Care Unit)"
    },
    {
        "id": "NEONATAL_REFUSAL_TO_FEED",
        "name": "Newborn Inability to Suckle / Feed",
        "kannada": "ನವಜಾತ ಶಿಶು ಹಾಲು ಕುಡಿಯಲು ನಿರಾಕರಿಸುತ್ತಿದೆ",
        "patterns": [r"\bunable to feed\b", r"\bnot suckling\b", r"ಹಾಲು ಕುಡಿಯುತ್ತಿಲ್ಲ", r"ಹಾಲು ಬಿಟ್ಟಿದೆ"],
        "category": "Neonatal",
        "severity": "CRITICAL",
        "action": "Urgent referral to SNCU / Pediatrician"
    }
]


class ASHAExtractionEngine:
    """
    Automated Healthcare Information Extraction Engine for ASHA Sahayak.
    Converts raw clinical narrative speech into structured field visit reports.
    """

    @classmethod
    def extract_report(cls, raw_transcript: str, language_code: str = "kn-IN") -> Dict[str, Any]:
        """
        Main extraction entry point.
        Analyzes the narrative transcript and extracts all 13 standard clinical fields.
        """
        text = raw_transcript.strip()
        if not text:
            return cls._empty_report(raw_transcript)

        # 1. Beneficiary ID
        ben_id = cls._extract_beneficiary_id(text)

        # 2. Beneficiary Name & Age
        name = cls._extract_beneficiary_name(text)
        age = cls._extract_beneficiary_age(text)

        # 3. Visit Type
        visit_type = cls._extract_visit_type(text)

        # 4. Pregnancy Status
        pregnancy_status = cls._extract_pregnancy_status(text, visit_type)

        # 5. Gestational Age
        gestational_age = cls._extract_gestational_age(text)

        # 6. Infant Weight & Blood Pressure
        weight, is_vlbw = cls._extract_infant_weight(text)
        bp_value, is_high_bp = cls._extract_blood_pressure(text)

        # 7. Vaccinations (Due vs Given)
        vax_due, vax_given = cls._extract_vaccinations(text)

        # 8. Symptoms & Observations (separating positive symptoms from negations)
        symptoms_reported, negated_symptoms = cls._extract_symptoms(text)

        # 9. Next Visit Date
        next_visit = cls._extract_next_visit(text)

        # 10. Danger Signs & Red Flag Rules
        danger_signs = cls._evaluate_danger_signs(text, is_high_bp, is_vlbw)

        # 11. Referral Requirement
        referral_required = len(danger_signs) > 0 or is_high_bp or is_vlbw
        referral_facility = "Primary Health Centre (PHC) / 24x7 FRU Emergency" if referral_required else None

        # 12. Missing Fields calculation based on clinical context
        missing_fields = cls._identify_missing_fields(
            visit_type=visit_type,
            name=name,
            weight=weight,
            bp=bp_value,
            next_visit=next_visit,
            gestational_age=gestational_age
        )

        # 13. Confidence Score & Uncertainty Indicators
        confidence_score, uncertain_indicators = cls._calculate_confidence(
            text=text,
            name=name,
            weight=weight,
            bp=bp_value,
            missing_fields=missing_fields
        )

        # 14. Voice Readback Text (in English and Kannada)
        readback_en = cls._generate_readback_en(
            name=name,
            visit_type=visit_type,
            gestational_age=gestational_age,
            weight=weight,
            symptoms=symptoms_reported,
            negations=negated_symptoms,
            danger_signs=danger_signs,
            next_visit=next_visit
        )
        readback_kn = cls._generate_readback_kn(
            name=name,
            visit_type=visit_type,
            gestational_age=gestational_age,
            weight=weight,
            symptoms=symptoms_reported,
            negations=negated_symptoms,
            danger_signs=danger_signs,
            next_visit=next_visit
        )

        report = {
            "beneficiary_id": ben_id,
            "beneficiary_name": name,
            "age": age,
            "beneficiary_age": age,
            "visit_type": visit_type,
            "pregnancy_status": pregnancy_status,
            "gestational_age": gestational_age,
            "weight": weight,
            "infant_weight": weight,
            "blood_pressure": bp_value,
            "vaccinations_due": vax_due,
            "immunization_details": vax_due,
            "vaccinations_given": vax_given,
            "symptoms": symptoms_reported,
            "symptoms_reported": symptoms_reported,
            "negated_symptoms": negated_symptoms,
            "next_visit_date": next_visit,
            "danger_signs": danger_signs,
            "referral_required": referral_required,
            "referral_facility": referral_facility,
            "missing_fields": missing_fields,
            "uncertain_indicators": uncertain_indicators,
            "confidence_score": confidence_score,
            "confirmed": False,
            "raw_transcript": text,
            "readback_en": readback_en,
            "readback_kn": readback_kn,
            "created_at": datetime.datetime.now().isoformat()
        }

        return report

    @classmethod
    def apply_voice_correction(cls, current_report: Dict[str, Any], correction_text: str) -> Tuple[Dict[str, Any], str, str]:
        """
        Parses a spoken correction (e.g., 'No, the weight is 2.8 kilograms' or 'ತೂಕ 2.8 ಕೆಜಿ').
        Updates ONLY the targeted field in the existing report.
        Returns: (updated_report, modified_field_name, readback_confirmation)
        """
        updated = dict(current_report)
        text = correction_text.strip()
        field_modified = "unknown"
        readback_confirm = ""

        # Case 1: Weight correction
        weight_match = re.search(r"\b(\d{1,2}(?:\.\d{1,2})?)\s*(?:kg|grams?|ಕೆಜಿ|ಕಿಲೋಗ್ರಾಂ|kilograms?)\b", text, re.IGNORECASE)
        if weight_match or "weight" in text.lower() or "ತೂಕ" in text:
            if weight_match:
                new_weight = f"{weight_match.group(1)} kg"
                updated["infant_weight"] = new_weight
                field_modified = "infant_weight"
                readback_confirm = f"Infant weight updated to {new_weight}. ತೂಕವನ್ನು {new_weight} ಗೆ ನವೀಕರಿಸಲಾಗಿದೆ. Is this correct?"

        # Case 2: Blood Pressure correction
        bp_match = re.search(r"\b(\d{2,3})\s*(?:/|by|\s)\s*(\d{2,3})\b", text)
        if bp_match or "bp" in text.lower() or "ಬಿಪಿ" in text:
            if bp_match:
                new_bp = f"{bp_match.group(1)}/{bp_match.group(2)}"
                updated["blood_pressure"] = new_bp
                field_modified = "blood_pressure"
                readback_confirm = f"Blood pressure updated to {new_bp}. ರಕ್ತದೊತ್ತಡ {new_bp} ಗೆ ನವೀಕರಿಸಲಾಗಿದೆ. Is this correct?"

        # Case 3: Beneficiary Name correction
        name_match = re.search(r"(?:name is|ಹೆಸರು|mother is|beneficiary is)\s+([A-Za-z\u0C80-\u0CFF]+)", text, re.IGNORECASE)
        if name_match:
            new_name = name_match.group(1).capitalize()
            updated["beneficiary_name"] = new_name
            field_modified = "beneficiary_name"
            readback_confirm = f"Beneficiary name updated to {new_name}. ಫಲಾನುಭವಿಯ ಹೆಸರು {new_name} ಗೆ ನವೀಕರಿಸಲಾಗಿದೆ."

        # Case 3b: Age correction
        age_match = re.search(r"(?:age\s+is|age|ವಯಸ್ಸು)\s*[:=]?\s*(\d{1,2})", text, re.IGNORECASE)
        if age_match:
            new_age = int(age_match.group(1))
            updated["age"] = new_age
            updated["beneficiary_age"] = new_age
            field_modified = "age"
            readback_confirm = f"Beneficiary age updated to {new_age}. ವಯಸ್ಸು {new_age} ಕ್ಕೆ ನವೀಕರಿಸಲಾಗಿದೆ."

        # Case 4: Next Visit Date correction
        if any(w in text.lower() for w in ["next visit", "ಮುಂದಿನ ಭೇಟಿ", "follow up", "next week", "ವಾರ"]):
            date_match = cls._extract_next_visit(text)
            if date_match:
                updated["next_visit_date"] = date_match
                field_modified = "next_visit_date"
                readback_confirm = f"Next visit date updated to {date_match}."

        # Case 5: Negated symptom correction (e.g. 'No fever' / 'ಜ್ವರ ಇಲ್ಲ')
        if any(w in text.lower() for w in ["no fever", "ಜ್ವರ ಇಲ್ಲ", "no headache", "ತಲೆನೋವು ಇಲ್ಲ"]):
            symptoms, negations = cls._extract_symptoms(text)
            for s in negations:
                clean_s = s.replace("No ", "")
                if clean_s in updated.get("symptoms_reported", []):
                    updated["symptoms_reported"].remove(clean_s)
                if s not in updated.get("negated_symptoms", []):
                    updated["negated_symptoms"].append(s)
            field_modified = "symptoms"
            readback_confirm = f"Symptoms updated. Negative symptoms noted. ಲಕ್ಷಣಗಳನ್ನು ನವೀಕರಿಸಲಾಗಿದೆ."

        # Re-evaluate danger signs & missing fields after correction
        is_high_bp = False
        if updated.get("blood_pressure"):
            parts = updated["blood_pressure"].split("/")
            if len(parts) == 2 and int(parts[0]) >= 140:
                is_high_bp = True

        is_vlbw = False
        if updated.get("infant_weight"):
            w_val = float(updated["infant_weight"].replace("kg", "").strip())
            if w_val < 2.0:
                is_vlbw = True

        updated["danger_signs"] = cls._evaluate_danger_signs(
            updated.get("raw_transcript", "") + " " + text,
            is_high_bp=is_high_bp,
            is_vlbw=is_vlbw
        )
        updated["referral_required"] = len(updated["danger_signs"]) > 0 or is_high_bp or is_vlbw

        # Refresh missing fields
        updated["missing_fields"] = cls._identify_missing_fields(
            visit_type=updated["visit_type"],
            name=updated["beneficiary_name"],
            weight=updated["infant_weight"],
            bp=updated["blood_pressure"],
            next_visit=updated["next_visit_date"],
            gestational_age=updated["gestational_age"]
        )

        return updated, field_modified, readback_confirm

    # ==========================================================================
    # Internal Extraction Utilities
    # ==========================================================================
    @staticmethod
    def _extract_beneficiary_id(text: str) -> Optional[str]:
        # Regex for ID patterns: RCH1234, KA-5829, ID 402, Thayi Card 9821
        m = re.search(r"\b(?:RCH|KA|MCP|ID|CARD|ತಾಯಿ ಕಾರ್ಡ್)?[\s\-_#:]*(\d{4,12})\b", text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
        return None

    @staticmethod
    def _extract_beneficiary_name(text: str) -> Optional[str]:
        # 1. Look for explicit patterns in English and Kannada
        patterns = [
            r"\b(?:smt\.?|mrs\.?|ms\.?|kumari|shri)\s+([A-Za-z\u0C80-\u0CFF]+)",
            r"(?:beneficiary\s+name\s+is|beneficiary\s+name|beneficiary\s+is|beneficiary)\s*[:=]?\s*(?:(?:smt\.?|mrs\.?|ms\.?|kumari|shri)\s+)?([A-Za-z\u0C80-\u0CFF]+)",
            r"(?:mother['’]?s\s+name\s+is|mother['’]?s\s+name|mother\s+is|mother)\s*[:=]?\s*(?:(?:smt\.?|mrs\.?|ms\.?|kumari|shri)\s+)?([A-Za-z\u0C80-\u0CFF]+)",
            r"(?:patient\s+name\s+is|patient\s+name|patient\s+is|patient)\s*[:=]?\s*(?:(?:smt\.?|mrs\.?|ms\.?|kumari|shri)\s+)?([A-Za-z\u0C80-\u0CFF]+)",
            r"(?:name\s+is|name)\s*[:=]?\s*(?:(?:smt\.?|mrs\.?|ms\.?|kumari|shri)\s+)?([A-Za-z\u0C80-\u0CFF]+)",
            r"(?:ಫಲಾನುಭವಿಯ\s+ಹೆಸರು|ಫಲಾನುಭವಿ|ತಾಯಿಯ\s+ಹೆಸರು|ತಾಯಿ|ಮಗುವಿನ\s+ತಾಯಿ|ಗರ್ಭಿಣಿ|ರೋಗಿಯ\s+ಹೆಸರು|ಹೆಸರು)\s*[:=]?\s*(?:(?:ಶ್ರೀಮತಿ|ಕುಮಾರಿ)\s+)?([A-Za-z\u0C80-\u0CFF]+)",
        ]
        
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw_name = m.group(1).strip()
                # Clean vibhakti endings
                raw_name = re.sub(r"(?:ಯವರಿಗೆ|ಅವರಿಗೆ|ರವರು|ಯವರ|ರಿಗೆ|ಗೆ|ಯಿಂದ|'s)$", "", raw_name)
                # Check Kannada map
                if raw_name in KANNADA_NAMES_MAP:
                    return KANNADA_NAMES_MAP[raw_name]
                for kn_base, en_base in KANNADA_NAMES_MAP.items():
                    if kn_base in raw_name:
                        return en_base
                # Avoid capturing stop words and titles
                if raw_name.lower() not in ("smt", "mrs", "ms", "kumari", "shri", "age", "weight", "visit", "is", "was", "the", "a", "an", "and", "bp", "ಫಲಾನುಭವಿ", "ಹೆಸರು"):
                    return raw_name.capitalize()

        # 2. Check dictionary of common names
        for kn_name, en_name in KANNADA_NAMES_MAP.items():
            if kn_name in text:
                return en_name

        for name in COMMON_FEMALE_NAMES:
            if re.search(rf"\b{name}\b", text, re.IGNORECASE):
                return name

        return None

    @staticmethod
    def _extract_beneficiary_age(text: str) -> Optional[int]:
        """Extracts beneficiary age (12-95 years) avoiding confusion with gestational weeks/months."""
        explicit_patterns = [
            r"(?:beneficiary\s+age(?:\s+is)?|age(?:\s+is)?|age\s*[:=])\s*(\d{1,2})\s*(?:years?|yrs?|ವರ್ಷ)?\b",
            r"(?:ವಯಸ್ಸು(?:\s*[:=]|ಯು)?)\s*(\d{1,2})\s*(?:ವರ್ಷ|years?|yrs?)?\b",
            r"\b(\d{1,2})\s*(?:years?\s+old|year\s+old|ವರ್ಷದ\s*ವಯಸ್ಸು|ವರ್ಷ\s*ವಯಸ್ಸು)\b",
        ]
        for pat in explicit_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    val = int(m.group(1))
                    if 12 <= val <= 95:
                        return val
                except ValueError:
                    pass

        # Suffix with "years" or "ವರ್ಷ" if not immediately preceded/followed by gestational terms
        for m in re.finditer(r"\b(\d{1,2})\s*(?:ವರ್ಷ|years?|yrs?)\b", text, re.IGNORECASE):
            start = max(0, m.start() - 6)
            end = min(len(text), m.end() + 6)
            surrounding = text[start:end].lower()
            if any(w in surrounding for w in ["week", "ವಾರ", "month", "ತಿಂಗಳು", "kg", "ಕೆಜಿ"]):
                continue
            try:
                val = int(m.group(1))
                if 12 <= val <= 95:
                    return val
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_visit_type(text: str) -> str:
        clean = text.lower()
        if any(w in clean for w in ["pnc", "postpartum", "ಹೆರಿಗೆ ನಂತರ", "delivery done", "ಬಾಣಂತಿ"]):
            return "PNC Home Visit (ಬಾಣಂತಿ ಭೇಟಿ)"
        if any(w in clean for w in ["anc", "pregnancy", "trimester", "ಗರ್ಭಿಣಿ", "ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ"]):
            return "ANC Home Visit (ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ)"
        if any(w in clean for w in ["vaccine", "vaccination", "immunization", "ಲಸಿಕೆ"]):
            return "Immunization Visit (ಲಸಿಕಾ ಭೇಟಿ)"
        if any(w in clean for w in ["newborn", "infant", "baby care", "ನವಜಾತ ಶಿಶು"]):
            return "Newborn Care Visit (ನವಜಾತ ಶಿಶು ಭೇಟಿ)"
        return "Routine Field Visit (ಸಾಮಾನ್ಯ ಭೇಟಿ)"

    @staticmethod
    def _extract_pregnancy_status(text: str, visit_type: str) -> Optional[str]:
        clean = text.lower()
        if any(w in clean for w in ["pregnant", "ಗರ್ಭಿಣಿ", "trimester", "anc"]) or "ANC" in visit_type:
            return "Pregnant (ಗರ್ಭಿಣಿ)"
        if any(w in clean for w in ["delivered", "postpartum", "ಹೆರಿಗೆ ಆಗಿದೆ", "ಬಾಣಂತಿ"]) or "PNC" in visit_type:
            return "Postpartum / Delivered (ಹೆರಿಗೆಯಾಗಿದೆ)"
        return None

    @staticmethod
    def _extract_gestational_age(text: str) -> Optional[str]:
        m_weeks = re.search(r"\b(\d{1,2})\s*(?:weeks?|ವಾರಗಳು|ವಾರ)", text, re.IGNORECASE)
        if m_weeks:
            return f"{m_weeks.group(1)} weeks ({m_weeks.group(1)} ವಾರಗಳು)"
        m_months = re.search(r"\b(\d{1,2})\s*(?:months?|ತಿಂಗಳುಗಳು|ತಿಂಗಳು)", text, re.IGNORECASE)
        if m_months:
            return f"{m_months.group(1)} months ({m_months.group(1)} ತಿಂಗಳು)"
        return None

    @staticmethod
    def _extract_infant_weight(text: str) -> Tuple[Optional[str], bool]:
        m = re.search(r"\b(\d{1,2}(?:\.\d{1,2})?)\s*(?:kg|grams?|ಕೆಜಿ|ಕಿಲೋಗ್ರಾಂ|kilograms?)\b", text, re.IGNORECASE)
        if m:
            val_str = m.group(1)
            try:
                val = float(val_str)
                is_vlbw = val < 2.0
                return f"{val} kg", is_vlbw
            except ValueError:
                pass
        return None, False

    @staticmethod
    def _extract_blood_pressure(text: str) -> Tuple[Optional[str], bool]:
        m = re.search(r"\b(\d{2,3})[/\s](\d{2,3})\b", text)
        if m:
            sys_val = int(m.group(1))
            dia_val = int(m.group(2))
            is_high = sys_val >= 140 or dia_val >= 90
            return f"{sys_val}/{dia_val}", is_high
        return None, False

    @classmethod
    def _extract_vaccinations(cls, text: str) -> Tuple[List[str], List[str]]:
        due_list = []
        given_list = []
        
        # Sentences split
        sentences = re.split(r"[।\.\n,]", text)
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue
                
            is_given = any(w in sentence_clean.lower() for w in ["given", "completed", "done", "ನೀಡಲಾಗಿದೆ", "ಕೊಟ್ಟಿದ್ದಾರೆ", "ಹಾಕಲಾಗಿದೆ"])
            is_due = any(w in sentence_clean.lower() for w in ["due", "pending", "ಬೇಕು", "ಮಾಡಬೇಕು", "ಹಾಕಿಸಬೇಕು", "ಬಾಕಿ"])
            
            for vax_name, patterns in VACCINE_CATALOG:
                matched = any(re.search(pat, sentence_clean, re.IGNORECASE) for pat in patterns)
                if matched:
                    if is_given and vax_name not in given_list:
                        given_list.append(vax_name)
                    elif (is_due or not is_given) and vax_name not in due_list:
                        due_list.append(vax_name)

        return due_list, given_list

    @classmethod
    def _is_negated_locally(cls, text: str, match_start: int, match_end: int) -> bool:
        """
        Determines whether a clinical mention at text[match_start:match_end] is negated.
        Handles Kannada and English phrasing such as:
          - "ರಕ್ತಸ್ರಾವ ಇಲ್ಲ" (negated)
          - "ತಲೆನೋವು ಇದೆ" (affirmed, not negated)
          - "no bleeding", "absent", "without fever" (negated)
        """
        # Look ahead up to 35 characters
        after_chunk = text[match_end:min(len(text), match_end + 35)]
        # If immediately followed by an affirmative marker, it is reported (not negated)
        if re.search(r"^\s*(?:ಇದೆ|ಆಗಿದೆ|ಕಂಡುಬಂದಿದೆ|ಇದ್ದಾರೆ|ಹೌದು|present|yes)\b", after_chunk, re.IGNORECASE):
            return False

        # Look behind up to 35 characters
        before_chunk = text[max(0, match_start - 35):match_start]
        if re.search(r"\b(?:having|has|complaints?\s+of)\s*$", before_chunk, re.IGNORECASE):
            if not re.search(r"\bnot\s+(?:having|has)\s*$", before_chunk, re.IGNORECASE):
                return False

        neg_words = [r"\bno\b", r"\bnot\b", r"\bnone\b", r"\bwithout\b", r"\bdenies\b", r"\babsent\b", r"ಇಲ್ಲ", r"ಆಗಿಲ್ಲ", r"ಬೇಡ", r"ಕಾಣುತ್ತಿಲ್ಲ"]

        # Words after (within 2 words)
        words_after = after_chunk.strip().split()
        if words_after:
            first_two = words_after[:2]
            if any(any(re.search(nw, w, re.IGNORECASE) for nw in neg_words) for w in first_two):
                return True

        # Words before (within 2 words)
        words_before = before_chunk.strip().split()
        if words_before:
            last_two = words_before[-2:]
            if any(any(re.search(nw, w, re.IGNORECASE) for nw in neg_words) for w in last_two):
                return True

        return False

    @classmethod
    def _extract_symptoms(cls, text: str) -> Tuple[List[str], List[str]]:
        reported = []
        negated = []

        # Split on clause / sentence boundaries
        clauses = re.split(r"[।\.\n,;]|(?:\b(?:and|but|ಆದರೆ|ಮತ್ತು)\b)", text, flags=re.IGNORECASE)
        for clause in clauses:
            clause_clean = clause.strip()
            if not clause_clean:
                continue

            # Ignore questions / hypothetical conditions
            if "?" in clause_clean or any(q in clause_clean for q in ["ಇದೆಯೇ", "ಆಗಿದೆಯೇ", "ಇದ್ದರೆ", "ಬಂದರೆ", "if", "whether"]):
                continue

            for symptom_name, patterns in SYMPTOMS_CATALOG:
                matched_in_clause = False
                for pat in patterns:
                    for m in re.finditer(pat, clause_clean, re.IGNORECASE):
                        matched_in_clause = True
                        is_neg = cls._is_negated_locally(clause_clean, m.start(), m.end())
                        if is_neg:
                            neg_label = f"No {symptom_name} ({symptom_name} ಇಲ್ಲ)"
                            if neg_label not in negated:
                                negated.append(neg_label)
                        else:
                            if symptom_name not in reported:
                                reported.append(symptom_name)
                        break
                    if matched_in_clause:
                        break

        # Remove from reported if it was also recorded in negated
        for n in negated:
            for s in list(reported):
                if s in n:
                    reported.remove(s)

        return reported, negated

    @staticmethod
    def _extract_next_visit(text: str) -> Optional[str]:
        m_week = re.search(r"(?:next\s+week|ಮುಂದಿನ\s+ವಾರ)", text, re.IGNORECASE)
        if m_week:
            return "Next Week (ಮುಂದಿನ ವಾರ)"
        m_days = re.search(r"(\d+)\s*(?:days?|ದಿನಗಳ)\s*(?:after|later|ನಂತರ)", text, re.IGNORECASE)
        if m_days:
            return f"After {m_days.group(1)} days ({m_days.group(1)} ದಿನಗಳ ನಂತರ)"
        m_month = re.search(r"(?:next\s+month|ಮುಂದಿನ\s+ತಿಂಗಳು)", text, re.IGNORECASE)
        if m_month:
            return "Next Month (ಮುಂದಿನ ತಿಂಗಳು)"
        return None

    @classmethod
    def _evaluate_danger_signs(cls, text: str, is_high_bp: bool, is_vlbw: bool) -> List[Dict[str, Any]]:
        signs = []
        
        # Check rule patterns
        for rule in DANGER_SIGN_RULES:
            if rule["id"] == "HIGH_BP":
                if is_high_bp:
                    signs.append(rule)
            elif rule["id"] == "VERY_LOW_BIRTH_WEIGHT":
                if is_vlbw:
                    signs.append(rule)
            else:
                for pat in rule["patterns"]:
                    matched_pattern = False
                    for m in re.finditer(pat, text, re.IGNORECASE):
                        if not cls._is_negated_locally(text, m.start(), m.end()):
                            if rule not in signs:
                                signs.append(rule)
                            matched_pattern = True
                            break
                    if matched_pattern:
                        break

        return signs

    @staticmethod
    def _identify_missing_fields(visit_type: str, name: Optional[str], weight: Optional[str],
                                 bp: Optional[str], next_visit: Optional[str],
                                 gestational_age: Optional[str]) -> List[str]:
        missing = []
        if not name:
            missing.append("beneficiary_name")
        if not next_visit:
            missing.append("next_visit_date")

        if "ANC" in visit_type:
            if not bp:
                missing.append("blood_pressure")
            if not gestational_age:
                missing.append("gestational_age")

        if "Newborn" in visit_type or "Infant" in visit_type:
            if not weight:
                missing.append("infant_weight")

        return missing

    @staticmethod
    def _calculate_confidence(text: str, name: Optional[str], weight: Optional[str],
                             bp: Optional[str], missing_fields: List[str]) -> Tuple[float, List[str]]:
        uncertain = []
        score = 0.95

        if not name:
            uncertain.append("Beneficiary name not clearly specified in narrative")
            score -= 0.15

        if len(missing_fields) > 2:
            uncertain.append(f"{len(missing_fields)} recommended clinical fields are missing")
            score -= 0.10

        if len(text.split()) < 6:
            uncertain.append("Short transcript; some clinical context may be incomplete")
            score -= 0.15

        return round(max(0.40, score), 2), uncertain

    @staticmethod
    def _generate_readback_en(name: Optional[str], visit_type: str, gestational_age: Optional[str],
                              weight: Optional[str], symptoms: List[str], negations: List[str],
                              danger_signs: List[Dict[str, Any]], next_visit: Optional[str]) -> str:
        parts = []
        parts.append(f"Beneficiary {name or 'unspecified'}." )
        parts.append(f"{visit_type}.")
        if gestational_age:
            parts.append(f"Gestational age {gestational_age}.")
        if weight:
            parts.append(f"Weight {weight}.")
        if symptoms:
            parts.append(f"Reported symptoms: {', '.join(symptoms)}.")
        if negations:
            parts.append(f"Confirmed absent: {', '.join(negations)}.")
        if danger_signs:
            parts.append(f"Alert: {danger_signs[0]['name']}. Immediate referral required.")
        if next_visit:
            parts.append(f"Next visit: {next_visit}.")
        parts.append("Is this information correct?")
        return " ".join(parts)

    @staticmethod
    def _generate_readback_kn(name: Optional[str], visit_type: str, gestational_age: Optional[str],
                              weight: Optional[str], symptoms: List[str], negations: List[str],
                              danger_signs: List[Dict[str, Any]], next_visit: Optional[str]) -> str:
        parts = []
        parts.append(f"ಫಲಾನುಭವಿ {name or 'ಹೆಸರು ದಾಖಲಾಗಿಲ್ಲ'}.")
        parts.append(f"{visit_type}.")
        if gestational_age:
            parts.append(f"ಗರ್ಭಾವಸ್ಥೆ {gestational_age}.")
        if weight:
            parts.append(f"ತೂಕ {weight}.")
        if symptoms:
            parts.append(f"ವರದಿಯಾದ ಲಕ್ಷಣಗಳು: {', '.join(symptoms)}.")
        if negations:
            parts.append(f"ಇಲ್ಲದಿರುವುದು: {', '.join(negations)}.")
        if danger_signs:
            parts.append(f"ಎಚ್ಚರಿಕೆ: {danger_signs[0]['kannada']}. ತುರ್ತು ಆಸ್ಪತ್ರೆಗೆ ಕಳುಹಿಸಬೇಕು.")
        if next_visit:
            parts.append(f"ಮುಂದಿನ ಭೇಟಿ: {next_visit}.")
        parts.append("ಈ ಮಾಹಿತಿ ಸರಿಯಾಗಿದೆಯೇ?")
        return " ".join(parts)

    @staticmethod
    def _empty_report(raw: str) -> Dict[str, Any]:
        return {
            "beneficiary_id": None,
            "beneficiary_name": None,
            "age": None,
            "beneficiary_age": None,
            "visit_type": "Unspecified Field Visit",
            "pregnancy_status": None,
            "gestational_age": None,
            "weight": None,
            "infant_weight": None,
            "blood_pressure": None,
            "vaccinations_due": [],
            "immunization_details": [],
            "vaccinations_given": [],
            "symptoms": [],
            "symptoms_reported": [],
            "negated_symptoms": [],
            "next_visit_date": None,
            "danger_signs": [],
            "referral_required": False,
            "referral_facility": None,
            "missing_fields": ["beneficiary_name", "visit_type"],
            "uncertain_indicators": ["Transcript is empty"],
            "confidence_score": 0.0,
            "confirmed": False,
            "raw_transcript": raw,
            "readback_en": "No speech recorded. Please record the visit again.",
            "readback_kn": "ಯಾವುದೇ ಧ್ವನಿ ದಾಖಲಾಗಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ರೆಕಾರ್ಡ್ ಮಾಡಿ.",
            "created_at": datetime.datetime.now().isoformat()
        }
