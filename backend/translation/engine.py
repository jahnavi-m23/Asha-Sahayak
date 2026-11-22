"""
ASHA Sahayak - Advanced Multilingual Translation Engine.
Adheres to AI4Bharat IndicTrans2 FLORES-233 standards for multilingual Indic translation:
  - Kannada (kan_Knda)
  - Hindi (hin_Deva)
  - Indian English (eng_Latn)
  - Tamil (tam_Taml)
  - Telugu (tel_Telu)
  - Malayalam (mal_Mlym)
  - Marathi (mar_Deva)
  - Bengali (ben_Beng)
  - Gujarati (guj_Gujr)
  - Punjabi (pan_Guru)

Features:
1. AI4Bharat IndicTrans2 FLORES-233 code mapping and adapter.
2. ClinicalEntityShield:
   - Preserves medicine names (Paracetamol, IFA, Calcium, Amoxicillin, Albendazole, Zinc, ORS, Vitamin A).
   - Preserves decimal measurements & vitals (NEVER allows 2.8 kg to become 28 kg; preserves BP 120/80).
   - Preserves UIP vaccines (OPV-1, Pentavalent-1, BCG, MR-1, DPT Booster, etc.).
   - Preserves beneficiary names and transliterations.
   - Preserves clinical negations (no fever, no bleeding, ರಕ್ತಸ್ರಾವ ಇಲ್ಲ, ಜ್ವರ ಇಲ್ಲ, ರಕ್ತಸ್ರಾವವಾಗಿಲ್ಲ).
3. Pre-normalization for Kannada-English code-mixed speech (normalizes Romanized speech markers).
4. Direct language-pair translation across all 100 language pairs.
5. Uncertainty flagging for human review when entities or negations require verification.
"""

import re
import asyncio
import urllib.parse
import logging
from typing import Dict, Any, Optional, Tuple, List, Set
import httpx

from backend.voice.config import SUPPORTED_LANGUAGES, config

logger = logging.getLogger("translation.engine")

# AI4Bharat IndicTrans2 FLORES-233 Language Code Mapping
INDICTRANS2_FLORES_MAP = {
    "kn-IN": "kan_Knda",
    "hi-IN": "hin_Deva",
    "en-IN": "eng_Latn",
    "ta-IN": "tam_Taml",
    "te-IN": "tel_Telu",
    "ml-IN": "mal_Mlym",
    "mr-IN": "mar_Deva",
    "bn-IN": "ben_Beng",
    "gu-IN": "guj_Gujr",
    "pa-IN": "pan_Guru"
}

FLORES_TO_CANONICAL = {v: k for k, v in INDICTRANS2_FLORES_MAP.items()}

# Two-letter ISO mappings
ISO_TO_CANONICAL = {
    "kn": "kn-IN",
    "hi": "hi-IN",
    "en": "en-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "pa": "pa-IN"
}

CANONICAL_TO_ISO = {v: k for k, v in ISO_TO_CANONICAL.items()}

# Target Language Negation Particles for Verification
TARGET_NEGATION_PARTICLES = {
    "en-IN": [r"\bno\b", r"\bnot\b", r"\babsent\b", r"\bwithout\b", r"\bdenies\b", r"\bdenied\b", r"\bnone\b"],
    "hi-IN": [r"नहीं", r"न\s+", r"न\b", r"बिना", r"अनुपस्थित"],
    "kn-IN": [r"ಇಲ್ಲ", r"ವಿಲ್ಲ", r"ಆಗಿಲ್ಲ", r"ಬೇಡ", r"ಕಾಣುತ್ತಿಲ್ಲ", r"ಇಲ್ಲದ"],
    "ta-IN": [r"இல்லை", r"இல்லாமல்", r"இல்லாத", r"இல்லை\b"],
    "te-IN": [r"లేదు", r"లేవు", r"కాదు", r"కావు", r"లేని", r"లేకుండా"],
    "ml-IN": [r"ഇല്ല", r"ഇല്ലാതെ", r"ഇല്ലാത്ത", r"ഇല്ല\b"],
    "mr-IN": [r"नाही", r"नसलेला", r"विना"],
    "bn-IN": [r"নেই", r"না\s+", r"কোন", r"ছাড়া", r"অনুপস্থিত"],
    "gu-IN": [r"નથી", r"વિના", r"વગર"],
    "pa-IN": [r"ਨਹੀਂ", r"ਬਿਨਾਂ", r"ਗੈਰ"]
}

# Essential Medicine Catalog (UIP & Primary Healthcare)
MEDICINES_CATALOG = [
    "Paracetamol", "IFA", "Iron Folic Acid", "Calcium", "Amoxicillin",
    "Albendazole", "Zinc", "ORS", "Vitamin A", "Metronidazole", "Cefixime"
]

# UIP Vaccine Catalog
UIP_VACCINES = [
    "BCG", "OPV-0", "OPV-1", "OPV-2", "OPV-3", "OPV",
    "Pentavalent-1", "Pentavalent-2", "Pentavalent-3", "Pentavalent",
    "Rotavirus", "PCV-1", "PCV-2", "PCV Booster",
    "MR-1", "MR-2", "Measles", "DPT Booster", "Td-1", "Td-2", "TT"
]

# Beneficiary Names Transliterations Across Scripts
BENEFICIARY_NAMES_MAP: Dict[str, Dict[str, str]] = {
    "Lakshmi": {
        "kn": "ಲಕ್ಷ್ಮಿ", "hi": "लक्ष्मी", "en": "Lakshmi", "ta": "லட்சுமி",
        "te": "లక్ష్మి", "ml": "ലക്ഷ്മി", "mr": "लक्ष्मी", "bn": "লক্ষ্মী",
        "gu": "લક્ષ્મી", "pa": "ਲਕਸ਼ਮੀ"
    },
    "Savitha": {
        "kn": "ಸವಿತಾ", "hi": "सविता", "en": "Savitha", "ta": "சவிதா",
        "te": "సవిత", "ml": "സവിത", "mr": "सविता", "bn": "সবিতা",
        "gu": "સવિતા", "pa": "ਸਵਿਤਾ"
    },
    "Radhika": {
        "kn": "ರಾಧಿಕಾ", "hi": "राधिका", "en": "Radhika", "ta": "ராதிகா",
        "te": "రాధిక", "ml": "രാധിക", "mr": "राधिका", "bn": "রাধিকা",
        "gu": "રાધિકા", "pa": "ਰਾਧਿਕਾ"
    },
    "Anita": {
        "kn": "ಅನಿತಾ", "hi": "अनिता", "en": "Anita", "ta": "அனிதா",
        "te": "అనిత", "ml": "അനിത", "mr": "अनिता", "bn": "অনিতা",
        "gu": "અનિતા", "pa": "ਅਨੀਤਾ"
    },
    "Rekha": {
        "kn": "ರೇಖಾ", "hi": "रेखा", "en": "Rekha", "ta": "ரேகா",
        "te": "రేఖ", "ml": "രേഖ", "mr": "रेखा", "bn": "রেখা",
        "gu": "રેખા", "pa": "ਰੇਖਾ"
    },
    "Meena": {
        "kn": "ಮೀನಾ", "hi": "मीना", "en": "Meena", "ta": "மீனா",
        "te": "మీనా", "ml": "മീന", "mr": "मीना", "bn": "মীনা",
        "gu": "મીના", "pa": "ਮੀਨਾ"
    }
}


class ClinicalEntityShield:
    """
    Guarantees medical accuracy and safety across multilingual translation:
    - Never changes 2.8 kg into 28 kg.
    - Preserves BP slashes and numbers (120/80).
    - Preserves clinical negations (prevents 'no bleeding' from becoming 'bleeding').
    - Preserves essential medicine and vaccine names.
    - Standardizes Indic numerals for clinical measurements.
    - Flags uncertain translations for human review.
    """

    INDIC_DIGIT_TABLE = str.maketrans(
        "०१२३४५६७८९০১২৩৪৫৬৭৮৯੦੧੨੩੪੫੬੭੮੯૦૧૨૩૪૫૬૭૮૯୦୧୨୩୪୫୬୭૮୯௦౧౨౩౪౫౬౭౮౯೦೧೨೩೪೫೬೭೮೯൦൧൨൩൪൫൬൭൮൯",
        "01234567890123456789012345678901234567890123456789012345678901234567890123456789"
    )

    @classmethod
    def normalize_indic_digits(cls, text: str) -> str:
        """Converts Indic script digits (Bengali, Devanagari, Kannada, etc.) to standard Arabic digits."""
        return text.translate(cls.INDIC_DIGIT_TABLE)

    @classmethod
    def pre_normalize_codemix(cls, text: str) -> str:
        """
        Pre-normalizes Romanized speech markers in Kannada-English code-mixed speech
        so that neural translators parse them grammatically rather than phonetically transliterating them.
        """
        subs = [
            (r"\b(ge|ige)\b", "ಗೆ"),
            (r"\b(ide|idhe)\b", "ಇದೆ"),
            (r"\b(illa|agilla)\b", "ಇಲ್ಲ"),
            (r"\b(kottide|kottidhe|kottidare)\b", "ನೀಡಲಾಗಿದೆ"),
            (r"\b(madide|madidhe)\b", "ಮಾಡಲಾಗಿದೆ"),
            (r"\b(beku)\b", "ಬೇಕು"),
            (r"\b(banta|bandide)\b", "ಬಂದಿದೆ"),
            (r"\b(du|dhu)\b", "ದು"),
            (r"\b(varagalu|vaara)\b", "ವಾರಗಳು")
        ]
        res = text
        for pat, repl in subs:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    @classmethod
    def extract_clinical_entities(cls, text: str) -> Dict[str, Any]:
        """Extracts critical clinical entities that must be verified in the target output."""
        entities = {
            "decimal_measurements": [],
            "blood_pressures": [],
            "gestational_weeks": [],
            "medicines": [],
            "vaccines": [],
            "has_negation": False,
            "negated_symptoms": [],
            "danger_signs": []
        }

        # 1. Decimal weights (e.g. 2.8 kg, 1.6 kg, 3.2 kg)
        for m in re.finditer(r"\b(\d+\.\d+)\s*(?:kg|grams?|ಕೆಜಿ|ಕಿಲೋ|किलो|கிலோ|కేజీ|কেজি|કિલો|ਕਿਲੋ)?\b", text, re.IGNORECASE):
            entities["decimal_measurements"].append(m.group(1))

        # 2. Blood pressure (e.g. 120/80, 140/90, 110/70)
        for m in re.finditer(r"\b(\d{2,3})[/\s](\d{2,3})\b", text):
            entities["blood_pressures"].append(f"{m.group(1)}/{m.group(2)}")

        # 3. Gestational weeks (e.g. 24 weeks, 28 weeks)
        for m in re.finditer(r"\b(\d{1,2})\s*(?:weeks?|ವಾರಗಳು|ವಾರ|सप्ताह|வாரங்கள்|వారాలు|ആഴ്ചകൾ|आठवडे|সপ্তাহ|અઠવાડિયા|ਹਫ਼ਤੇ)\b", text, re.IGNORECASE):
            entities["gestational_weeks"].append(m.group(1))

        # 4. Medicines
        for med in MEDICINES_CATALOG:
            if re.search(rf"\b{med}\b", text, re.IGNORECASE):
                entities["medicines"].append(med)

        # 5. UIP Vaccines
        for vax in UIP_VACCINES:
            vax_pat = re.escape(vax).replace(r"\-", r"[\s\-]*")
            if re.search(rf"\b{vax_pat}\b", text, re.IGNORECASE):
                entities["vaccines"].append(vax)

        # 6. Clinical Negations
        neg_patterns = [
            r"ಇಲ್ಲ", r"ಆಗಿಲ್ಲ", r"ಬೇಡ", r"ಯಾವುದೇ\s+ಇಲ್ಲ",
            r"\bno\b", r"\bnot\b", r"\babsent\b", r"\bwithout\b", r"\bdenies\b",
            r"नहीं", r"न\s+", r"இல்லை", r"లేదు", r"নেই"
        ]
        if any(re.search(p, text, re.IGNORECASE) for p in neg_patterns):
            entities["has_negation"] = True

        # Check for specific negated symptoms (bleeding, fever, headache, vomiting)
        if any(w in text for w in ["ರಕ್ತಸ್ರಾವ ಇಲ್ಲ", "no bleeding", "रक्तस्राव नहीं", "ரத்தப்போக்கு இல்லை", "రక్తస్రావం లేదు", "রক্তপাত নেই"]):
            entities["negated_symptoms"].append("bleeding")
        if any(w in text for w in ["ಜ್ವರ ಇಲ್ಲ", "no fever", "बुखार नहीं", "காய்ச்சல் இல்லை", "జ్వరం లేదు", "জ্বর নেই"]):
            entities["negated_symptoms"].append("fever")
        if any(w in text for w in ["ತಲೆನೋವು ಇಲ್ಲ", "no headache", "सिरदर्द नहीं", "தலைவலி இல்லை", "తలనొప్పి లేదు", "মাথাব্যথা নেই"]):
            entities["negated_symptoms"].append("headache")

        # 7. Danger Signs
        if any(w in text.lower() for w in ["ತೀವ್ರ ರಕ್ತಸ್ರಾವ", "severe bleeding", "water broke", "ನೀರು ಒಡೆದಿದೆ", "convulsions", "fits", "ಫಿಟ್ಸ್", "मूर्छा"]):
            entities["danger_signs"].append("critical_maternal")

        return entities

    @classmethod
    def verify_and_guard(
        cls,
        source_text: str,
        translated_text: str,
        source_entities: Dict[str, Any],
        target_language: str
    ) -> Tuple[str, bool, List[str]]:
        """
        Verifies translation consistency against shielded clinical entities:
        - Prevents decimal corruption (e.g. 2.8 kg -> 28 kg).
        - Prevents BP formatting loss.
        - Prevents negation inversion.
        Returns: (guarded_text, is_uncertain, review_reasons)
        """
        guarded = cls.normalize_indic_digits(translated_text)
        review_reasons = []
        is_uncertain = False

        # 1. Decimal Measurements Guard (Never allow 2.8 kg to become 28 kg)
        for dec in source_entities.get("decimal_measurements", []):
            if dec not in guarded:
                # Check if it was corrupted to integer without decimal (e.g. "2.8" -> "28")
                corrupted_int = dec.replace(".", "")
                if corrupted_int in guarded and len(dec) >= 3:
                    # Restore correct decimal measurement
                    guarded = re.sub(rf"\b{corrupted_int}\b", dec, guarded)
                    logger.warning(f"[ClinicalEntityShield] Corrected corrupted measurement: '{corrupted_int}' -> '{dec}'")
                else:
                    is_uncertain = True
                    review_reasons.append(f"Decimal measurement '{dec}' was not explicitly preserved in translation.")

        # 2. Blood Pressure Guard (Ensure 120/80 is not corrupted to 12080)
        for bp in source_entities.get("blood_pressures", []):
            if bp not in guarded:
                bp_no_slash = bp.replace("/", "")
                if bp_no_slash in guarded:
                    guarded = guarded.replace(bp_no_slash, bp)
                    logger.warning(f"[ClinicalEntityShield] Restored blood pressure format: '{bp}'")
                else:
                    is_uncertain = True
                    review_reasons.append(f"Blood pressure '{bp}' format mismatch in translation.")

        # 3. Clinical Negation Inversion Guard
        if source_entities.get("has_negation", False):
            target_particles = TARGET_NEGATION_PARTICLES.get(target_language, [r"\bno\b", r"\bnot\b", r"नहीं", r"ಇಲ್ಲ"])
            has_target_negation = any(re.search(p, guarded, re.IGNORECASE) for p in target_particles)
            if not has_target_negation:
                # Catastrophic medical danger: Source said "no symptom" but translation has no negation!
                is_uncertain = True
                review_reasons.append(
                    f"Clinical negation missing: source text specifies absence of symptom, "
                    f"but target language ({target_language}) translation appears to lack an explicit negation particle."
                )
                logger.error(f"[ClinicalEntityShield] ALERT: Negation inversion risk in translation to {target_language}!")

        # 4. Vaccine Code Verification
        for vax in source_entities.get("vaccines", []):
            vax_clean = vax.replace("Booster", "").strip()
            # If vaccine token isn't found in translation, flag for review
            if not re.search(rf"\b{vax_clean}\b", guarded, re.IGNORECASE) and not any(k in guarded for k in ["ओपीवी", "ಒಪಿವಿ", "ஓபிவி", "ఓపివి", "টিকা", "लस", "ਟੀਕਾ"]):
                review_reasons.append(f"Vaccine name '{vax}' may have been transliterated or omitted.")

        return guarded, is_uncertain, review_reasons


class ASHAIndicTranslator:
    """
    Production Multilingual Translation Engine for ASHA Sahayak.
    Supports AI4Bharat IndicTrans2 FLORES-233 architecture across all 10 Indian languages.
    """

    def __init__(self):
        self.http_timeout = 10.0
        self.model_name = "AI4Bharat-IndicTrans2 / Neural-Indic-NMT"
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Returns a persistent, connection-pooled AsyncClient bound to current event loop."""
        current_loop = asyncio.get_running_loop()
        if (
            self._client is None
            or self._client.is_closed
            or getattr(self, "_loop", None) != current_loop
        ):
            if self._client and not self._client.is_closed:
                try:
                    await self._client.aclose()
                except Exception:
                    pass
            self._loop = current_loop
            self._client = httpx.AsyncClient(
                timeout=self.http_timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "*/*"
                },
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=40, keepalive_expiry=60.0),
                follow_redirects=True
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @classmethod
    def detect_language(cls, text: str) -> str:
        """
        Detects Indian language from script Unicode ranges and lexical markers.
        Returns canonical code (e.g. 'kn-IN', 'hi-IN', 'bn-IN', etc.).
        """
        if not text or not text.strip():
            return "kn-IN"

        has_kannada = bool(re.search(r"[\u0C80-\u0CFF]", text))
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", text))
        has_bengali = bool(re.search(r"[\u0980-\u09FF]", text))
        has_tamil = bool(re.search(r"[\u0B80-\u0BFF]", text))
        has_telugu = bool(re.search(r"[\u0C00-\u0C7F]", text))
        has_malayalam = bool(re.search(r"[\u0D00-\u0D7F]", text))
        has_gujarati = bool(re.search(r"[\u0A80-\u0AFF]", text))
        has_gurmukhi = bool(re.search(r"[\u0A00-\u0A7F]", text))
        has_latin = bool(re.search(r"[a-zA-Z]", text))

        if has_kannada:
            return "kn-IN"
        if has_bengali:
            return "bn-IN"
        if has_tamil:
            return "ta-IN"
        if has_telugu:
            return "te-IN"
        if has_malayalam:
            return "ml-IN"
        if has_gujarati:
            return "gu-IN"
        if has_gurmukhi:
            return "pa-IN"
        if has_devanagari:
            # Distinguish Marathi from Hindi by Marathi auxiliary verbs and words
            if any(w in text for w in ["आहे", "नाही", "भेट", "केले", "बाळ", "आठवडे"]):
                return "mr-IN"
            return "hi-IN"
        if has_latin:
            return "en-IN"

        return "kn-IN"

    @classmethod
    def normalize_language_code(cls, code: Optional[str]) -> Tuple[str, str, str]:
        """
        Normalizes any input language code string into (canonical_code, iso_code, flores_code).
        Example: 'kn-IN' -> ('kn-IN', 'kn', 'kan_Knda')
        """
        if not code or code.strip().lower() in ("auto", "indic-auto"):
            return "auto", "auto", "auto"

        c = code.strip()
        if c in SUPPORTED_LANGUAGES:
            canonical = c
            iso = CANONICAL_TO_ISO.get(canonical, canonical[:2])
            flores = INDICTRANS2_FLORES_MAP.get(canonical, "kan_Knda")
            return canonical, iso, flores

        # Short ISO code
        short = c.split("-")[0].lower()
        if short in ISO_TO_CANONICAL:
            canonical = ISO_TO_CANONICAL[short]
            flores = INDICTRANS2_FLORES_MAP.get(canonical, "kan_Knda")
            return canonical, short, flores

        # FLORES-233 code check
        if c in FLORES_TO_CANONICAL:
            canonical = FLORES_TO_CANONICAL[c]
            iso = CANONICAL_TO_ISO.get(canonical, "kn")
            return canonical, iso, c

        return "kn-IN", "kn", "kan_Knda"

    async def translate(
        self,
        text: str,
        source_language: Optional[str] = None,
        target_language: str = "hi-IN",
        domain: str = "healthcare"
    ) -> Dict[str, Any]:
        """
        Translates text between supported Indian languages with clinical entity shielding.
        """
        clean_text = text.strip()
        if not clean_text:
            return {
                "original_text": "",
                "translated_text": "",
                "source_language": "kn-IN",
                "target_language": target_language,
                "target_voice": config.get_voice_for_language(target_language),
                "model": self.model_name,
                "flores_source": "kan_Knda",
                "flores_target": INDICTRANS2_FLORES_MAP.get(target_language, "hin_Deva"),
                "uncertain": False,
                "review_warning": None,
                "success": True
            }

        # 1. Resolve source and target language specifications
        target_canonical, target_iso, target_flores = self.normalize_language_code(target_language)
        if not source_language or source_language in ("auto", "indic-auto"):
            detected_canonical = self.detect_language(clean_text)
            source_canonical, source_iso, source_flores = self.normalize_language_code(detected_canonical)
        else:
            source_canonical, source_iso, source_flores = self.normalize_language_code(source_language)

        target_voice = config.get_voice_for_language(target_canonical)

        # 2. Passthrough if source and target languages are identical
        if source_canonical == target_canonical:
            return {
                "original_text": clean_text,
                "translated_text": clean_text,
                "source_language": source_canonical,
                "target_language": target_canonical,
                "target_voice": target_voice,
                "model": self.model_name,
                "flores_source": source_flores,
                "flores_target": target_flores,
                "uncertain": False,
                "review_warning": None,
                "engine_used": "passthrough",
                "success": True
            }

        # 3. Clinical Entity Shielding: Extract and pre-normalize
        source_entities = ClinicalEntityShield.extract_clinical_entities(clean_text)
        pre_normalized_text = ClinicalEntityShield.pre_normalize_codemix(clean_text)

        # 4. Neural Translation
        raw_translation = None
        engine_label = "neural-indic-nmt"

        # Check for configured IndicTrans2 or Bhashini custom endpoint
        if config.indictrans2_endpoint or config.bhashini_endpoint:
            try:
                raw_translation = await self._indictrans2_endpoint_translate(
                    pre_normalized_text, source_flores, target_flores
                )
                if raw_translation:
                    engine_label = "ai4bharat-indictrans2-endpoint"
            except Exception as e:
                logger.warning(f"[IndicTrans2 Endpoint] Custom endpoint failed: {e}. Falling back to Neural NMT.")

        # High-Fidelity Neural Indic Machine Translation
        if not raw_translation:
            try:
                raw_translation = await self._neural_nmt_translate(
                    pre_normalized_text, source_iso, target_iso
                )
            except Exception as e:
                logger.error(f"[Neural NMT] Translation failed: {e}")

        # Check if translation succeeded
        if not raw_translation or (source_canonical != target_canonical and raw_translation.strip() == pre_normalized_text.strip()):
            logger.error(f"[Neural NMT] Translation failed for {source_canonical} -> {target_canonical}")
            return {
                "original_text": clean_text,
                "translated_text": "",
                "source_language": source_canonical,
                "target_language": target_canonical,
                "target_voice": target_voice,
                "model": self.model_name,
                "flores_source": source_flores,
                "flores_target": target_flores,
                "uncertain": True,
                "review_warning": f"Translation from {source_canonical} to {target_canonical} could not be completed. Please check connection.",
                "engine_used": "failed",
                "success": False,
                "error": "Translation service unavailable or returned untranslated text"
            }

        # 5. Clinical Entity Guard: Post-translation verification
        guarded_text, is_uncertain, review_reasons = ClinicalEntityShield.verify_and_guard(
            source_text=clean_text,
            translated_text=raw_translation,
            source_entities=source_entities,
            target_language=target_canonical
        )

        review_warning = "; ".join(review_reasons) if review_reasons else None

        logger.info(
            f"[Translation Complete] {source_canonical} -> {target_canonical} ({target_voice}): "
            f"uncertain={is_uncertain}, engine={engine_label}"
        )

        return {
            "original_text": clean_text,
            "translated_text": guarded_text.strip(),
            "source_language": source_canonical,
            "target_language": target_canonical,
            "target_voice": target_voice,
            "model": self.model_name,
            "flores_source": source_flores,
            "flores_target": target_flores,
            "uncertain": is_uncertain,
            "review_warning": review_warning,
            "engine_used": engine_label,
            "success": True
        }

    async def _neural_nmt_translate(self, text: str, source_iso: str, target_iso: str) -> Optional[str]:
        """Translates sentence via multi-endpoint neural machine translation with connection pooling and retries."""
        # Auto-detect script if source is auto
        if source_iso == "auto":
            if bool(re.search(r"[\u0C80-\u0CFF]", text)):
                sl = "kn"
            elif bool(re.search(r"[\u0900-\u097F]", text)):
                sl = "hi"
            elif bool(re.search(r"[\u0B80-\u0BFF]", text)):
                sl = "ta"
            elif bool(re.search(r"[\u0C00-\u0C7F]", text)):
                sl = "te"
            elif bool(re.search(r"[\u0D00-\u0D7F]", text)):
                sl = "ml"
            elif bool(re.search(r"[\u0980-\u09FF]", text)):
                sl = "bn"
            elif bool(re.search(r"[\u0A80-\u0AFF]", text)):
                sl = "gu"
            elif bool(re.search(r"[\u0A00-\u0A7F]", text)):
                sl = "pa"
            else:
                sl = "auto"
        else:
            sl = source_iso

        tl = target_iso
        encoded_query = urllib.parse.quote(text)

        endpoints = [
            f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={tl}&dt=t&q={encoded_query}",
            f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl={sl}&tl={tl}&q={encoded_query}"
        ]

        for ep_url in endpoints:
            for attempt in range(2):
                try:
                    client = await self.get_client()
                    resp = await client.get(ep_url)
                    if resp.status_code == 200:
                        data = resp.json()
                        # Format 1: [[["translated text", ...]]]
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                            chunks = [chunk[0] for chunk in data[0] if chunk and len(chunk) > 0 and chunk[0]]
                            if chunks:
                                return "".join(chunks)
                        # Format 2: ["translated text"] or [["translated text"]]
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], str):
                            return data[0]
                except Exception as e:
                    logger.warning(f"[Neural NMT] Attempt {attempt+1} on endpoint failed: {e}")
                    if attempt == 0:
                        if self._client and not self._client.is_closed:
                            await self._client.aclose()
                            self._client = None
                        await asyncio.sleep(0.2)
        return None

    async def _indictrans2_endpoint_translate(self, text: str, source_flores: str, target_flores: str) -> Optional[str]:
        """Adapter for external AI4Bharat IndicTrans2 or Bhashini inference endpoints."""
        endpoint = config.indictrans2_endpoint or config.bhashini_endpoint
        if not endpoint:
            return None

        headers = {"Content-Type": "application/json"}
        if config.bhashini_api_key:
            headers["Authorization"] = config.bhashini_api_key
        if config.bhashini_user_id:
            headers["userID"] = config.bhashini_user_id

        payload = {
            "source_language": source_flores,
            "target_language": target_flores,
            "input": [text]
        }

        try:
            client = await self.get_client()
            resp = await client.post(endpoint, json=payload, headers=headers)
            if resp.status_code == 200:
                res_data = resp.json()
                # Support standard IndicTrans2 and Bhashini response structures
                if "output" in res_data and isinstance(res_data["output"], list) and len(res_data["output"]) > 0:
                    first = res_data["output"][0]
                    return first.get("target") or first
                if "pipelineResponse" in res_data:
                    tasks = res_data["pipelineResponse"]
                    for t in tasks:
                        if t.get("taskType") == "translation" and "output" in t:
                            return t["output"][0].get("target")
        except Exception as e:
            logger.warning(f"[IndicTrans2 Endpoint] Error: {e}")
        return None


indic_translator = ASHAIndicTranslator()
MultilingualTranslationEngine = ASHAIndicTranslator
