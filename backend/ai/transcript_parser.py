# backend/ai/transcript_parser.py
"""
Multilingual transcript parsing and entity preservation.
Handles:
- Kannada, English, and Kannada-English code-mix (knglish).
- Preserves medical terminology, measurements, age, dates, and vaccination names.
- Regex-based weight and age extraction.
- Kannada numerals (೦, ೧, ೨, ೩, ೪, ೫, ೬, ೭, ೮, ೯) and spoken number words.
- Detection and flagging of incomplete, ambiguous, or uncertain statements.
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any

from backend.ai.medical_vocab import (
    STANDARDIZED_VACCINES,
    GENERIC_VACCINE_CLASSES,
    VISIT_TYPE_PATTERNS,
    KANNADA_DIGITS_MAP,
    KANNADA_SPOKEN_NUMBERS,
    AGE_UNITS_MAP,
    UNCERTAINTY_INDICATORS
)


class TranscriptParser:
    """Pre-processes raw ASHA worker transcripts using rule & regex extraction."""

    @staticmethod
    def normalize_transcript(text: str) -> str:
        """Clean noise, normalize whitespace, replace Kannada digits."""
        if not text:
            return ""

        # Replace Kannada digits with ASCII digits
        for kn_digit, ascii_digit in KANNADA_DIGITS_MAP.items():
            text = text.replace(kn_digit, ascii_digit)

        # Remove audio artifacts like (cough), [laughter], "uh", "um"
        text = re.sub(r"\[.*?\]|\(.*?\)", "", text)
        text = re.sub(r"\b(uh|um|er|ah|ಅಂದರೆ|ಅಂದ್ರೆ)\b", "", text, flags=re.IGNORECASE)

        # Standardize punctuation and spaces
        text = re.sub(r"\s+", " ", text).strip()
        text = text.strip(" ,;:.-")
        return text

    @staticmethod
    def extract_weight(text: str) -> Optional[str]:
        """
        Regex-based weight extraction from English, Kannada, or code-mixed text.
        Examples:
        - "3.2 kg" -> "3.2 kg"
        - "weight is 2.8 kilograms" -> "2.8 kg"
        - "ತೂಕ ೩.೨ ಕೆಜಿ" -> "3.2 kg"
        - "baby weight 3.2" -> "3.2 kg"
        - "ಮೂರು point ಎರಡು ಕೆಜಿ" -> "3.2 kg"
        - "3200 grams" -> "3.20 kg"
        """
        clean = TranscriptParser.normalize_transcript(text).lower()

        # Check for spoken numbers like "ಮೂರು point ಎರಡು ಕೆಜಿ" (3.2 kg)
        words = clean.split()
        for i in range(len(words) - 2):
            w1, w2, w3 = words[i], words[i+1], words[i+2]
            if w1 in KANNADA_SPOKEN_NUMBERS and w2 in ("point", "ಪಾಯಿಂಟ್", ".") and w3 in KANNADA_SPOKEN_NUMBERS:
                n1 = KANNADA_SPOKEN_NUMBERS[w1]
                n3 = KANNADA_SPOKEN_NUMBERS[w3]
                return f"{n1}.{n3} kg"

        # Regex patterns for weight with units
        patterns = [
            # 3.2 kg / 3.2 kilograms / 3.2 kgs / 3.2 grams
            r"(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilogram|kilograms|ಕೆಜಿ|ಕಿಲೋಗ್ರಾಂ|ಕಿಲೋ)",
            # weight is 3.2 / weight: 3.2 / ತೂಕ 3.2 / ತೂಕ: 3.2
            r"(?:weight|wt|ತೂಕ|thooka)(?:\s*(?:is|ಆಗಿದೆ|ide|:))?\s*(\d+(?:\.\d+)?)",
            # baby weight 3.2
            r"baby\s+weight\s*(?:is)?\s*(\d+(?:\.\d+)?)",
            # grams: 3200 g
            r"(\d+)\s*(?:grams|gram|g|ಗ್ರಾಂ)",
        ]

        for pat in patterns:
            match = re.search(pat, clean)
            if match:
                val = match.group(1)
                try:
                    num_val = float(val)
                    if "gram" in match.group(0) or "ಗ್ರಾಂ" in match.group(0):
                        if num_val >= 500:
                            return f"{num_val / 1000.0:.2f} kg"
                    # Biological plausibility check (0.5 kg to 150 kg)
                    if 0.5 <= num_val <= 150.0:
                        return f"{num_val} kg"
                except ValueError:
                    pass

        return None

    @staticmethod
    def extract_age(text: str) -> Optional[str]:
        """
        Regex-based age extraction for infants, children, or mothers.
        Examples:
        - "6 weeks old" -> "6 weeks"
        - "2 months baby" -> "2 months"
        - "10 days" -> "10 days"
        - "೧೦ ದಿನದ ಮಗು" -> "10 days"
        - "ಆರು ವಾರ" -> "6 weeks"
        - "೨ ತಿಂಗಳು" -> "2 months"
        - "1 year" -> "1 year"
        """
        clean = TranscriptParser.normalize_transcript(text).lower()

        # Check spoken Kannada numbers with units: e.g. "ಆರು ವಾರ", "ಎರಡು ತಿಂಗಳು"
        for spoken_word, digit in KANNADA_SPOKEN_NUMBERS.items():
            if digit == ".":
                continue
            for kn_unit, std_unit in AGE_UNITS_MAP.items():
                pattern = rf"\b{re.escape(spoken_word)}\s+{re.escape(kn_unit)}(?:ದ)?\b"
                if re.search(pattern, clean):
                    unit_singular = std_unit[:-1] if digit == "1" else std_unit
                    return f"{digit} {unit_singular}"

        # Standard numeric patterns: "6 weeks", "2 months", "10 days", "1 year", "೨ ತಿಂಗಳು"
        age_pattern = r"(\d+)\s*(days?|weeks?|months?|years?|ದಿನಗಳು|ದಿನ|ವಾರಗಳು|ವಾರ|ತಿಂಗಳುಗಳು|ತಿಂಗಳು|ವರ್ಷಗಳು|ವರ್ಷ|dina|vaara|tingalu|varsha)(?:ದ)?"
        match = re.search(age_pattern, clean)
        if match:
            num = match.group(1)
            raw_unit = match.group(2).lower()
            std_unit = AGE_UNITS_MAP.get(raw_unit, "months")
            # Pluralize/singularize correctly
            if num == "1" and std_unit.endswith("s"):
                std_unit = std_unit[:-1]
            return f"{num} {std_unit}"

        return None

    @staticmethod
    def extract_vaccinations(text: str) -> List[str]:
        """
        Detect and standardize vaccination mentions using the UIP dictionary.
        Strictly excludes negated mentions (e.g. 'not OPV-1', 'OPV-1 alla', 'OPV-1 illa').
        """
        clean = TranscriptParser.normalize_transcript(text).lower()
        detected = []

        # Sort keys by length descending to match multi-word expressions and specific doses first
        sorted_vaccine_keys = sorted(STANDARDIZED_VACCINES.keys(), key=len, reverse=True)

        for v_key in sorted_vaccine_keys:
            pattern = r"(?:\b|_)" + re.escape(v_key) + r"(?:\b|_)"
            if re.search(pattern, clean) or v_key in clean:
                # Check for negation directly before or after
                start_indices = [m.start() for m in re.finditer(re.escape(v_key), clean)]
                is_neg = False
                for s_idx in start_indices:
                    e_idx = s_idx + len(v_key)
                    pre_tokens = clean[max(0, s_idx - 20):s_idx].strip().split()
                    post_tokens = clean[e_idx:min(len(clean), e_idx + 20)].strip().split()
                    if any(w in ["not", "no", "never", "without", "ಅಲ್ಲ"] for w in pre_tokens[-2:]):
                        is_neg = True
                        break
                    if any(w in ["alla", "illa", "ಅಲ್ಲ", "ಇಲ್ಲ"] for w in post_tokens[:2]):
                        is_neg = True
                        break

                if not is_neg:
                    std_name = STANDARDIZED_VACCINES[v_key]
                    # If specific dose already detected (e.g., OPV-1), suppress generic (OPV)
                    is_generic_redundant = False
                    if std_name in GENERIC_VACCINE_CLASSES:
                        for existing in detected:
                            if existing.startswith(f"{std_name}-") or existing.startswith(f"{std_name} "):
                                is_generic_redundant = True
                                break
                    if not is_generic_redundant and std_name not in detected:
                        detected.append(std_name)

        return detected

    @staticmethod
    def extract_beneficiary_id(text: str) -> Optional[str]:
        """
        Extract beneficiary ID if explicitly mentioned in transcript.
        Never invent if absent!
        Patterns: BNF-1234, BNF2041, ID 2041, ASHA-BNF-01.
        """
        patterns = [
            r"\b(BNF-[0-9A-Za-z]+)\b",
            r"\b(BNF[0-9A-Za-z]+)\b",
            r"\bben(?:eficiary)?\s*(?:id|no|number)?\s*[:#-]?\s*([0-9A-Za-z-]+)\b",
            r"\bಫಲಾನುಭವಿ\s*(?:ಸಂಖ್ಯೆ|ಐಡಿ)?\s*[:#-]?\s*([0-9A-Za-z-]+)\b"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                val = match.group(1).upper().strip()
                if val.startswith("BNF-"):
                    return val
                elif val.startswith("BNF"):
                    return f"BNF-{val[3:]}"
                elif val.replace("-", "").isalnum():
                    return f"BNF-{val}"
                return val
        return None

    @staticmethod
    def extract_next_visit_date(text: str) -> Optional[str]:
        """
        Extract next scheduled visit date in standard YYYY-MM-DD format.
        Supports:
        - ISO format: 2026-11-28
        - DD/MM/YYYY or DD-MM-YYYY
        - Relative dates: "next week", "after 3 days", "3 ದಿನಗಳ ನಂತರ", "ನಾಳೆ", "tomorrow"
        """
        clean = TranscriptParser.normalize_transcript(text).lower()

        # 1. ISO format: 2026-11-28
        iso_match = re.search(r"\b(202\d-[0-1]\d-[0-3]\d)\b", clean)
        if iso_match:
            return iso_match.group(1)

        # 2. DD/MM/YYYY or DD-MM-YYYY
        dmy_match = re.search(r"\b([0-3]?\d)[/-]([0-1]?\d)[/-](202\d)\b", clean)
        if dmy_match:
            d, m, y = dmy_match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}"

        # 3. Relative date handling
        today = datetime.now()
        
        # Tomorrow / ನಾಳೆ
        if "tomorrow" in clean or "ನಾಳೆ" in clean or "naale" in clean:
            target = today + timedelta(days=1)
            return target.strftime("%Y-%m-%d")

        # Next week / ಮುಂದಿನ ವಾರ
        if "next week" in clean or "ಮುಂದಿನ ವಾರ" in clean or "mundina vaara" in clean:
            target = today + timedelta(days=7)
            return target.strftime("%Y-%m-%d")

        # After X days / X ದಿನಗಳ ನಂತರ
        days_after_match = re.search(r"(\d+)\s*(?:days?\s*(?:after|later)|ದಿನಗಳ?\s*ನಂತರ|dina\s*aadmele)", clean)
        if days_after_match:
            days = int(days_after_match.group(1))
            target = today + timedelta(days=days)
            return target.strftime("%Y-%m-%d")

        # After 1 month / ಒಂದು ತಿಂಗಳ ನಂತರ
        if "after 1 month" in clean or "ಒಂದು ತಿಂಗಳ ನಂತರ" in clean or "next month" in clean or "ಮುಂದಿನ ತಿಂಗಳು" in clean:
            target = today + timedelta(days=30)
            return target.strftime("%Y-%m-%d")

        return None

    @staticmethod
    def infer_visit_type(text: str) -> Optional[str]:
        """Infer visit type based on clinical vocabulary patterns."""
        clean = TranscriptParser.normalize_transcript(text).lower()
        for kw, v_type in VISIT_TYPE_PATTERNS.items():
            if kw in clean:
                return v_type
        return "Newborn home visit"  # Default context for postnatal/newborn register

    @staticmethod
    def detect_ambiguity_and_uncertainty(text: str) -> Tuple[bool, List[str]]:
        """
        Identify ambiguous, conflicting, cut-off, or uncertain statements.
        Flags them for human review rather than guessing.
        """
        clean = TranscriptParser.normalize_transcript(text).lower()
        uncertain_flags = []

        # 1. Check for hesitation or uncertainty words
        for indicator in UNCERTAINTY_INDICATORS:
            if re.search(rf"\b{re.escape(indicator)}\b", clean):
                uncertain_flags.append(f"uncertainty_modifier: '{indicator}'")
                break

        # 2. Check for ranges or conflicting values (e.g. "2.5 or 3 kg", "೨ ಅಥವಾ ೩ ಕೆಜಿ")
        if re.search(r"\d+(?:\.\d+)?\s*(?:or|to|ಅಥವಾ)\s*\d+(?:\.\d+)?\s*(?:kg|ಕೆಜಿ)", clean):
            uncertain_flags.append("conflicting_weight_range")

        # 3. Check for incomplete trailing speech
        incomplete_endings = ["...", "and", "then", "ಆದರೆ", "ಮತ್ತು", "weight is", "ತೂಕ", "age is"]
        for ending in incomplete_endings:
            if clean.endswith(ending):
                uncertain_flags.append("unclear_trailing_speech")
                break

        # 4. Check for field mentions without values
        if ("weight" in clean or "ತೂಕ" in clean) and not TranscriptParser.extract_weight(text):
            uncertain_flags.append("weight_unspecified")

        if ("vaccine" in clean or "injection" in clean or "ಲಸಿಕೆ" in clean) and not TranscriptParser.extract_vaccinations(text):
            uncertain_flags.append("vaccine_unspecified")

        return (len(uncertain_flags) > 0), uncertain_flags

    # Maintain backward compatibility
    detect_ambiguity_or_incompletion = detect_ambiguity_and_uncertainty
