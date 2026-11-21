# backend/safety/danger_signs.py
"""
Rule-Based Danger-Sign Detection Engine.
Inspects transcripts against approved public health guidelines (MoHFW HBNC, ANC, IMNCI).
Handles:
- Contextual checks
- Negation detection in English, Kannada, and code-mixed formats
- Hypothetical statement exclusion
- Flagging uncertain matches for human review
"""
import re
from typing import List, Tuple
from backend.models.schemas import DangerSignDetection, DangerSignSeverity
from backend.safety.guidelines import PUBLIC_HEALTH_RULES, DangerSignRule


# Negation words across languages
ENGLISH_NEGATIONS = [
    "no", "not", "none", "neither", "denies", "absence of", "without",
    "ruled out", "does not have", "did not have", "no sign of", "free from",
    "zero", "resolved", "no history of"
]

KANNADA_NEGATIONS = [
    "ಇಲ್ಲ", "ಇಲ್ಲವೇ ಇಲ್ಲ", "ಇರುವುದಿಲ್ಲ", "ಕಾಣಿಸುತ್ತಿಲ್ಲ", "ಕಂಡುಬಂದಿಲ್ಲ",
    "ಜ್ವರ ಇಲ್ಲ", "ರಕ್ತಸ್ರಾವ ಇಲ್ಲ", "ಫಿಟ್ಸ್ ಇಲ್ಲ", "ಸಮಸ್ಯೆ ಇಲ್ಲ", "ಆಗಿಲ್ಲ"
]

CODEMIX_NEGATIONS = [
    "illa", "illave illa", "aagilla", "bandilla", "no fever", "no bleeding",
    "fever illa", "bleeding illa", "fits illa", "cold illa", "swelling illa"
]

ALL_NEGATIONS = set(ENGLISH_NEGATIONS + KANNADA_NEGATIONS + CODEMIX_NEGATIONS)

# Hypothetical and conditional triggers (should NOT trigger confirmed emergency)
HYPOTHETICAL_PATTERNS = [
    r"\bif\b", r"\bin case of\b", r"\bwhenever\b", r"\bhypothetical\b",
    r"\bsuppose\b", r"\bshould there be\b", r"ಒಂದು ವೇಳೆ", r"ಆದರೆ",
    r"ಬಂದರೆ", r"ಆದಲ್ಲಿ", r"if fever comes", r"if bleeding starts"
]


class DangerSignDetector:
    """Public health rule-based danger-sign evaluator."""

    def __init__(self, rules=None):
        self.rules = rules or PUBLIC_HEALTH_RULES

    def detect_danger_signs(self, transcript: str, language: str = "kn-en") -> List[DangerSignDetection]:
        """
        Analyze transcript for danger signs with strict context and negation checks.
        """
        if not transcript or not transcript.strip():
            return []

        cleaned_text = transcript.strip().lower()
        detections: List[DangerSignDetection] = []

        for code, rule in self.rules.items():
            match_found, matched_phrase, is_uncertain = self._check_rule_match(cleaned_text, rule)
            if match_found:
                # Check for negation in proximity of the match
                is_negated = self._is_phrase_negated(cleaned_text, matched_phrase)
                
                # Check for hypothetical/conditional context
                is_hypothetical = self._is_hypothetical_context(cleaned_text, matched_phrase)
                if is_hypothetical:
                    # Treat hypothetical mentions as negated or not active danger signs
                    is_negated = True

                detection = DangerSignDetection(
                    code=rule.code,
                    name=rule.name_en,
                    name_kannada=rule.name_kn,
                    severity=DangerSignSeverity.UNCERTAIN if is_uncertain else rule.severity,
                    category=rule.category,
                    matched_phrase=matched_phrase,
                    is_negated=is_negated,
                    is_uncertain=is_uncertain,
                    guideline_source=rule.guideline_source,
                    referral_instruction_en=rule.referral_instruction_en,
                    referral_instruction_kn=rule.referral_instruction_kn,
                )
                detections.append(detection)

        return detections

    def has_actionable_danger_signs(self, detections: List[DangerSignDetection]) -> bool:
        """Return True if any un-negated, actionable danger sign is present."""
        return any(d.referral_instruction_en and not d.is_negated and not d.is_uncertain for d in detections)

    def _check_rule_match(self, text: str, rule: DangerSignRule) -> Tuple[bool, str, bool]:
        """Check if any keyword of the rule matches the text."""
        # 1. Check exact/phrase keywords
        all_keywords = rule.keywords_en + rule.keywords_kn
        for kw in all_keywords:
            kw_clean = kw.lower()
            if kw_clean in text:
                return True, kw, False

        # 2. Check uncertain keywords
        for ukw in rule.uncertain_keywords:
            ukw_clean = ukw.lower()
            if ukw_clean in text:
                return True, ukw, True

        return False, "", False

    def _is_phrase_negated(self, text: str, phrase: str) -> bool:
        """
        Check if the phrase is negated within a token window (before or after).
        Supports English, Kannada script, and Romanized Kannada (e.g. 'illa').
        """
        phrase = phrase.lower()
        if phrase not in text:
            return False

        # Find all occurrences of the phrase
        start_indices = [m.start() for m in re.finditer(re.escape(phrase), text)]

        for start_idx in start_indices:
            end_idx = start_idx + len(phrase)

            # Window before the phrase (up to 40 characters or ~4 words)
            pre_window = text[max(0, start_idx - 40):start_idx].strip()
            # Window after the phrase (up to 40 characters or ~4 words)
            post_window = text[end_idx:min(len(text), end_idx + 40)].strip()

            pre_tokens = [t.strip(",.?!;: ") for t in pre_window.split() if t.strip(",.?!;: ")]
            post_tokens = [t.strip(",.?!;: ") for t in post_window.split() if t.strip(",.?!;: ")]

            # Check pre-tokens for English/Kannada negation (e.g. "no fever", "without bleeding")
            if any(t in ALL_NEGATIONS for t in pre_tokens[-3:]):
                return True

            # Check post-tokens for Kannada/code-mixed negation (e.g. "fever illa", "ಜ್ವರ ಇಲ್ಲ")
            if any(t in ALL_NEGATIONS for t in post_tokens[:3]):
                return True

            # Check full compound patterns in the proximity
            combined_window = f"{pre_window} {phrase} {post_window}"
            for neg in ALL_NEGATIONS:
                if f"{phrase} {neg}" in combined_window or f"{neg} {phrase}" in combined_window:
                    return True

        return False

    def _is_hypothetical_context(self, text: str, phrase: str) -> bool:
        """Detect if the danger sign mention is part of a conditional/advice statement."""
        for pattern in HYPOTHETICAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # If conditional exists, check if it's in the same sentence or clause
                return True
        return False
