# backend/ai/medical_vocab.py
"""
ASHA SAHAYAK - Comprehensive Medical & Maternal-Child Health Vocabulary Dictionary.
Covers:
- Universal Immunization Programme (UIP) Vaccinations in India.
- Kannada script, English, and Romanized Kannada (code-mixed / Knglish).
- Maternal, newborn, and child health terms.
- Clinical symptoms, anatomy, measurements, numbers, and dates.
"""
from typing import Dict, List, Set


# -------------------------------------------------------------------------
# 1. STANDARDIZED UIP VACCINATION DICTIONARY
# -------------------------------------------------------------------------
# Maps spoken/text variants across English, Kannada script, and Romanized Kannada
# to official standardized Universal Immunization Programme (UIP) vaccine names.
STANDARDIZED_VACCINES: Dict[str, str] = {
    # --- Birth Doses ---
    "bcg": "BCG",
    "b.c.g.": "BCG",
    "b.c.g": "BCG",
    "ಬಿಸಿಜಿ": "BCG",
    "ಬಿಸಿಜಿ ಲಸಿಕೆ": "BCG",
    "bcg injection": "BCG",
    "bcg vaccine": "BCG",
    "bcg lasike": "BCG",

    "hepb": "Hepatitis B",
    "hepatitis b": "Hepatitis B",
    "hep b": "Hepatitis B",
    "ಹೆಪಟೈಟಿಸ್ ಬಿ": "Hepatitis B",
    "hepatitis b birth dose": "Hepatitis B",

    "opv-0": "OPV-0",
    "opv 0": "OPV-0",
    "opv zero": "OPV-0",
    "oral polio 0": "OPV-0",
    "ಒಪಿವಿ-0": "OPV-0",
    "ಒಪಿವಿ 0": "OPV-0",
    "ಜೀರೋ ಪೋಲಿಯೋ": "OPV-0",

    # --- OPV Primary & Booster ---
    "opv-1": "OPV-1",
    "opv 1": "OPV-1",
    "oral polio 1": "OPV-1",
    "ಒಪಿವಿ-1": "OPV-1",
    "ಒಪಿವಿ 1": "OPV-1",
    "opv one": "OPV-1",
    "polio 1": "OPV-1",

    "opv-2": "OPV-2",
    "opv 2": "OPV-2",
    "oral polio 2": "OPV-2",
    "ಒಪಿವಿ-2": "OPV-2",
    "ಒಪಿವಿ 2": "OPV-2",
    "opv two": "OPV-2",
    "polio 2": "OPV-2",

    "opv-3": "OPV-3",
    "opv 3": "OPV-3",
    "oral polio 3": "OPV-3",
    "ಒಪಿವಿ-3": "OPV-3",
    "ಒಪಿವಿ 3": "OPV-3",
    "opv three": "OPV-3",
    "polio 3": "OPV-3",

    "opv booster": "OPV-Booster",
    "opv-booster": "OPV-Booster",
    "polio booster": "OPV-Booster",
    "ಪೋಲಿಯೋ ಬೂಸ್ಟರ್": "OPV-Booster",

    "opv": "OPV",
    "oral polio": "OPV",
    "polio drops": "OPV",
    "polio drop": "OPV",
    "polio": "OPV",
    "ಪೋಲಿಯೋ": "OPV",
    "ಪೋಲಿಯೋ ಹನಿ": "OPV",
    "ಒಪಿವಿ": "OPV",

    # --- Pentavalent ---
    "penta-1": "Pentavalent-1",
    "penta 1": "Pentavalent-1",
    "pentavalent-1": "Pentavalent-1",
    "pentavalent 1": "Pentavalent-1",
    "ಪೆಂಟಾವಲೆಂಟ್-1": "Pentavalent-1",
    "ಪೆಂಟಾವಲೆಂಟ್ 1": "Pentavalent-1",
    "ಪೆಂಟಾ-1": "Pentavalent-1",
    "ಪೆಂಟಾ 1": "Pentavalent-1",

    "penta-2": "Pentavalent-2",
    "penta 2": "Pentavalent-2",
    "pentavalent-2": "Pentavalent-2",
    "pentavalent 2": "Pentavalent-2",
    "ಪೆಂಟಾವಲೆಂಟ್-2": "Pentavalent-2",
    "ಪೆಂಟಾವಲೆಂಟ್ 2": "Pentavalent-2",
    "ಪೆಂಟಾ-2": "Pentavalent-2",
    "ಪೆಂಟಾ 2": "Pentavalent-2",

    "penta-3": "Pentavalent-3",
    "penta 3": "Pentavalent-3",
    "pentavalent-3": "Pentavalent-3",
    "pentavalent 3": "Pentavalent-3",
    "ಪೆಂಟಾವಲೆಂಟ್-3": "Pentavalent-3",
    "ಪೆಂಟಾವಲೆಂಟ್ 3": "Pentavalent-3",
    "ಪೆಂಟಾ-3": "Pentavalent-3",
    "ಪೆಂಟಾ 3": "Pentavalent-3",

    "pentavalent": "Pentavalent",
    "penta": "Pentavalent",
    "ಪೆಂಟಾವಲೆಂಟ್": "Pentavalent",
    "ಪೆಂಟಾ": "Pentavalent",

    # --- Rotavirus ---
    "rotavirus-1": "Rotavirus-1",
    "rotavirus 1": "Rotavirus-1",
    "rota-1": "Rotavirus-1",
    "rota 1": "Rotavirus-1",
    "ರೋಟಾವೈರಸ್-1": "Rotavirus-1",
    "ರೋಟಾ-1": "Rotavirus-1",

    "rotavirus-2": "Rotavirus-2",
    "rotavirus 2": "Rotavirus-2",
    "rota-2": "Rotavirus-2",
    "ರೋಟಾವೈರಸ್-2": "Rotavirus-2",

    "rotavirus-3": "Rotavirus-3",
    "rotavirus 3": "Rotavirus-3",
    "rota-3": "Rotavirus-3",
    "ರೋಟಾವೈರಸ್-3": "Rotavirus-3",

    "rotavirus": "Rotavirus",
    "rota": "Rotavirus",
    "ರೋಟಾವೈರಸ್": "Rotavirus",
    "ರೋಟಾ": "Rotavirus",

    # --- fIPV / IPV ---
    "fipv-1": "fIPV-1",
    "fipv 1": "fIPV-1",
    "ipv-1": "fIPV-1",
    "ipv 1": "fIPV-1",
    "fractional ipv 1": "fIPV-1",
    "ಎಫ್ಐಪಿವಿ-1": "fIPV-1",
    "ಐಪಿವಿ-1": "fIPV-1",

    "fipv-2": "fIPV-2",
    "fipv 2": "fIPV-2",
    "ipv-2": "fIPV-2",
    "ipv 2": "fIPV-2",
    "ಎಫ್ಐಪಿವಿ-2": "fIPV-2",
    "ಐಪಿವಿ-2": "fIPV-2",

    "fipv": "fIPV",
    "ipv": "fIPV",
    "ಐಪಿವಿ": "fIPV",

    # --- Pneumococcal Conjugate Vaccine (PCV) ---
    "pcv-1": "PCV-1",
    "pcv 1": "PCV-1",
    "ಪಿಸಿವಿ-1": "PCV-1",
    "ಪಿಸಿವಿ 1": "PCV-1",

    "pcv-2": "PCV-2",
    "pcv 2": "PCV-2",
    "ಪಿಸಿವಿ-2": "PCV-2",
    "ಪಿಸಿವಿ 2": "PCV-2",

    "pcv booster": "PCV-Booster",
    "pcv-booster": "PCV-Booster",
    "ಪಿಸಿವಿ ಬೂಸ್ಟರ್": "PCV-Booster",

    "pcv": "PCV",
    "ಪಿಸಿವಿ": "PCV",

    # --- Measles-Rubella (MR) ---
    "mr-1": "MR-1",
    "mr 1": "MR-1",
    "measles rubella 1": "MR-1",
    "measles-rubella 1": "MR-1",
    "measles-rubella": "MR-1",
    "measles 1": "MR-1",
    "ಎಂಆರ್-1": "MR-1",
    "ಎಂಆರ್ 1": "MR-1",
    "ಮೀಸಲ್ಸ್ ರುಬೆಲ್ಲಾ": "MR-1",
    "ಮೀಸಲ್ಸ್": "MR-1",

    "mr-2": "MR-2",
    "mr 2": "MR-2",
    "measles rubella 2": "MR-2",
    "measles-rubella 2": "MR-2",
    "ಎಂಆರ್-2": "MR-2",
    "ಎಂಆರ್ 2": "MR-2",

    "mr": "MR-1",
    "measles": "MR-1",
    "ಎಂಆರ್": "MR-1",

    # --- Japanese Encephalitis (JE) ---
    "je-1": "JE-1",
    "je 1": "JE-1",
    "ಜೆಇ-1": "JE-1",

    "je-2": "JE-2",
    "je 2": "JE-2",
    "ಜೆಇ-2": "JE-2",

    "je": "JE",
    "ಜೆಇ": "JE",

    # --- DPT & Booster ---
    "dpt-booster-1": "DPT-Booster-1",
    "dpt booster 1": "DPT-Booster-1",
    "dpt booster-1": "DPT-Booster-1",
    "ಡಿಪಿಟಿ ಬೂಸ್ಟರ್ 1": "DPT-Booster-1",
    "ಡಿಪಿಟಿ-1": "DPT-Booster-1",

    "dpt-booster-2": "DPT-Booster-2",
    "dpt booster 2": "DPT-Booster-2",
    "ಡಿಪಿಟಿ ಬೂಸ್ಟರ್ 2": "DPT-Booster-2",
    "ಡಿಪಿಟಿ-2": "DPT-Booster-2",

    "dpt": "DPT",
    "ಡಿಪಿಟಿ": "DPT",

    # --- Vitamin A ---
    "vitamin a": "Vitamin A",
    "vitamin-a": "Vitamin A",
    "vit a": "Vitamin A",
    "ವಿಟಮಿನ್ ಎ": "Vitamin A",
    "ವಿಟಮಿನ್-ಎ": "Vitamin A",
    "ವಿಟಮಿನ್": "Vitamin A",

    # --- Tetanus & Diphtheria (Td) ---
    "td-1": "Td-1",
    "td 1": "Td-1",
    "ಟಿಡಿ-1": "Td-1",
    "ಟಿಡಿ 1": "Td-1",
    "tetanus 1": "Td-1",
    "tt 1": "Td-1",
    "tt-1": "Td-1",

    "td-2": "Td-2",
    "td 2": "Td-2",
    "ಟಿಡಿ-2": "Td-2",
    "ಟಿಡಿ 2": "Td-2",
    "tetanus 2": "Td-2",
    "tt 2": "Td-2",
    "tt-2": "Td-2",

    "td booster": "Td-Booster",
    "td-booster": "Td-Booster",
    "ಟಿಡಿ ಬೂಸ್ಟರ್": "Td-Booster",
    "tt booster": "Td-Booster",

    "td": "Td",
    "tt": "Td",
    "ಟಿಡಿ": "Td",
    "ಧನುರ್ವಾಯು": "Td",
}

# Generic base vaccine classes for deduplication (if a specific dose is present, suppress generic)
GENERIC_VACCINE_CLASSES: Set[str] = {
    "OPV", "Rotavirus", "Pentavalent", "fIPV", "PCV", "MR", "JE", "DPT", "Td"
}


# -------------------------------------------------------------------------
# 2. VISIT TYPES MAPPING
# -------------------------------------------------------------------------
VISIT_TYPE_PATTERNS: Dict[str, str] = {
    # Newborn / HBNC
    "newborn": "Newborn home visit",
    "baby": "Newborn home visit",
    "infant": "Newborn home visit",
    "hbnc": "Newborn home visit",
    "home visit": "Newborn home visit",
    "ಶಿಶು": "Newborn home visit",
    "ಮಗು": "Newborn home visit",
    "ನವಜಾತ": "Newborn home visit",
    "ಮನೆ ಭೇಟಿ": "Newborn home visit",
    "magu": "Newborn home visit",
    "shishu": "Newborn home visit",
    "navajata": "Newborn home visit",

    # Antenatal Care (ANC)
    "anc": "Antenatal Care (ANC)",
    "pregnancy": "Antenatal Care (ANC)",
    "pregnant": "Antenatal Care (ANC)",
    "antenatal": "Antenatal Care (ANC)",
    "trimester": "Antenatal Care (ANC)",
    "ಗರ್ಭಿಣಿ": "Antenatal Care (ANC)",
    "ಗರ್ಭಾವಸ್ಥೆ": "Antenatal Care (ANC)",
    "ತಾಯಿ ತಪಾಸಣೆ": "Antenatal Care (ANC)",
    "garbhini": "Antenatal Care (ANC)",

    # Postnatal Care (PNC)
    "pnc": "Postnatal Care (PNC)",
    "postnatal": "Postnatal Care (PNC)",
    "postpartum": "Postnatal Care (PNC)",
    "delivery": "Postnatal Care (PNC)",
    "puerperium": "Postnatal Care (PNC)",
    "ಬಾಣಂತಿ": "Postnatal Care (PNC)",
    "ಹೆರಿಗೆ": "Postnatal Care (PNC)",
    "ಹೆರಿಗೆಯ ನಂತರ": "Postnatal Care (PNC)",
    "bananti": "Postnatal Care (PNC)",
    "herige": "Postnatal Care (PNC)",

    # Routine Immunization
    "immunization": "Routine Immunization",
    "vaccine": "Routine Immunization",
    "vaccination": "Routine Immunization",
    "injection": "Routine Immunization",
    "ಲಸಿಕೆ": "Routine Immunization",
    "ಚುಚ್ಚುಮದ್ದು": "Routine Immunization",
    "lasike": "Routine Immunization",
    "teeka": "Routine Immunization",

    # Child Growth Monitoring
    "growth": "Child Growth Monitoring",
    "growth monitoring": "Child Growth Monitoring",
    "ಬೆಳವಣಿಗೆ": "Child Growth Monitoring",
    "belavanige": "Child Growth Monitoring",

    # General checkup
    "checkup": "Child health checkup",
    "check up": "Child health checkup",
    "ತಪಾಸಣೆ": "Child health checkup",
    "tapasane": "Child health checkup",
}


# -------------------------------------------------------------------------
# 3. NUMERALS & KANNADA NUMBER WORDS
# -------------------------------------------------------------------------
KANNADA_DIGITS_MAP: Dict[str, str] = {
    '೦': '0', '೧': '1', '೨': '2', '೩': '3', '೪': '4',
    '೫': '5', '೬': '6', '೭': '7', '೮': '8', '೯': '9'
}

KANNADA_SPOKEN_NUMBERS: Dict[str, str] = {
    "ಸೊನ್ನೆ": "0", "sonne": "0",
    "ಒಂದು": "1", "ondu": "1",
    "ಎರಡು": "2", "eradu": "2",
    "ಮೂರು": "3", "mooru": "3",
    "ನಾಲ್ಕು": "4", "naalku": "4",
    "ಐದು": "5", "aidu": "5",
    "ಆರು": "6", "aaru": "6",
    "ಏಳು": "7", "elu": "7",
    "ಎಂಟು": "8", "entu": "8",
    "ಒಂಬತ್ತು": "9", "ombattu": "9",
    "ಹತ್ತು": "10", "hattu": "10",
    "ಹನ್ನೊಂದು": "11", "hannondhu": "11",
    "ಹನ್ನೆರಡು": "12", "hanneradu": "12",
    "ಹದಿನಾಲ್ಕು": "14",
    "ಹದಿನೈದು": "15", "hadinaidu": "15",
    "ಇಪ್ಪತ್ತು": "20", "ippattu": "20",
    "ಮೂವತ್ತು": "30",
    "ಪಾಯಿಂಟ್": ".", "point": "."
}


# -------------------------------------------------------------------------
# 4. AGE UNITS & VOCABULARY
# -------------------------------------------------------------------------
AGE_UNITS_MAP: Dict[str, str] = {
    "day": "days",
    "days": "days",
    "ದಿನ": "days",
    "ದಿನಗಳು": "days",
    "dina": "days",

    "week": "weeks",
    "weeks": "weeks",
    "ವಾರ": "weeks",
    "ವಾರಗಳು": "weeks",
    "vaara": "weeks",

    "month": "months",
    "months": "months",
    "ತಿಂಗಳು": "months",
    "ತಿಂಗಳುಗಳು": "months",
    "tingalu": "months",

    "year": "years",
    "years": "years",
    "ವರ್ಷ": "years",
    "ವರ್ಷಗಳು": "years",
    "varsha": "years",
}


# -------------------------------------------------------------------------
# 5. AMBIGUITY, HESITATION & UNCERTAINTY MARKERS
# -------------------------------------------------------------------------
UNCERTAINTY_INDICATORS: List[str] = [
    # English
    "maybe", "perhaps", "doubtful", "not sure", "approximately", "approx",
    "around", "or maybe", "slightly", "mildly", "unclear", "guess", "could be",
    "either", "confused",
    # Kannada script
    "ಬಹುಶಃ", "ಸುಮಾರು", "ಸರಿಯಾಗಿ ಗೊತ್ತಿಲ್ಲ", "ಸಂದೇಹ", "ಸ್ವಲ್ಪ", "ಅಂದಾಜು", "ಗೊಂದಲ",
    # Romanized Kannada
    "bahusha", "sumaaru", "doubt ide", "sari gottilla", "swalpa", "andaaju", "maybe ide"
]
