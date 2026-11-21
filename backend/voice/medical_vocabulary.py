"""
ASHA Sahayak - Medical Vocabulary and Keyterm Prompting Registry.
Curated for rural healthcare field visits in Karnataka & pan-India.
Includes Kannada, English, and Kannada-English code-mixed medical terms.
"""

from typing import List, Dict, Tuple, Any, Optional

# ==============================================================================
# 1. Official Keyterm Hints for Gnani Prisma v3.0 (Strictly ASCII Compliant)
# ==============================================================================
# IMPORTANT: Under HTTP specifications (RFC 7230) and Gnani Prisma WebSocket
# gateway standards, HTTP upgrade headers MUST contain ONLY ASCII characters (0x20-0x7E).
# Passing non-ASCII Unicode characters (such as Kannada script) directly in HTTP
# headers causes websockets.exceptions.InvalidHeaderValue ("invalid keyterms header").
#
# Gnani Prisma v3.0 natively handles Kannada script recognition via its acoustic model.
# The WebSocket keyterms header is used to boost clinical acronyms, drug names,
# and standardized English/transliterated medical terminology.

# Core 15-20 most critical field terms across ASHA visits
CORE_MEDICAL_KEYTERMS_ASCII: List[str] = [
    "BCG", "OPV", "OPV-1", "Pentavalent", "Penta-1",
    "Rotavirus", "fIPV", "PCV", "MR", "DPT", "Td", "Vitamin A",
    "kg", "grams", "BP", "120/80", "IFA", "ORS", "Paracetamol",
    "Garbhini", "Thayi Card", "ASHA"
]

# Domain-specific ASCII keyterm sets for targeted recognition
DOMAIN_KEYTERMS_ASCII: Dict[str, List[str]] = {
    "vaccination": [
        "BCG", "OPV", "OPV-0", "OPV-1", "OPV-2", "OPV-3",
        "Pentavalent", "Penta-1", "Penta-2", "Penta-3",
        "Rotavirus", "Rota-1", "Rota-2", "Rota-3",
        "fIPV", "IPV", "PCV", "PCV-1", "PCV-2", "PCV Booster",
        "MR", "MR-1", "MR-2", "Measles Rubella", "JE",
        "DPT", "DPT Booster", "Td", "Td-1", "Td-2", "Tetanus",
        "Vitamin A", "Hep B", "Hepatitis B"
    ],
    "maternal": [
        "Garbhini", "ANC", "PNC", "Trimester",
        "LMP", "EDD", "Gestational", "Thayi Card",
        "MCP Card", "Anemia", "Hemoglobin", "High Risk Pregnancy",
        "Preeclampsia", "Edema", "Ultrasound", "Fetal Heart Rate",
        "Fetal Movement", "Herige", "Delivery",
        "Colostrum", "Exclusive Breastfeeding",
        "BP", "Blood Pressure", "120/80", "110/70", "130/90",
        "IFA", "Iron Folic Acid", "Calcium"
    ],
    "newborn": [
        "Navajata Shishu", "Birth Weight", "Low Birth Weight",
        "LBW", "kg", "grams", "Malnutrition", "SAM", "MAM",
        "Wasting", "Stunting", "KMC", "Kangaroo Mother Care",
        "Jaundice", "Cord Care", "Hypothermia", "Dehydration",
        "Colostrum", "Exclusive Breastfeeding",
        "BCG", "OPV-0", "Vitamin A"
    ],
    "vitals": [
        "BP", "Blood Pressure", "120/80", "110/70", "130/90", "140/90",
        "Pulse", "Temperature", "Fahrenheit", "Celsius",
        "kg", "grams", "cm", "Weeks", "Months",
        "Fever", "Cough", "Cold", "Vomiting", "Diarrhea", "Headache",
        "Bleeding", "Swelling", "Abdominal Pain",
        "ORS", "Paracetamol", "IFA"
    ],
    "general": CORE_MEDICAL_KEYTERMS_ASCII
}

# The comprehensive ASCII pool (up to 200 terms, strictly validated ASCII)
MEDICAL_KEYTERMS_200: List[str] = [
    # Vaccines & Immunization
    "BCG", "OPV", "OPV-0", "OPV-1", "OPV-2", "OPV-3",
    "Pentavalent", "Penta-1", "Penta-2", "Penta-3",
    "Rotavirus", "Rota-1", "Rota-2", "Rota-3",
    "fIPV", "IPV", "PCV", "PCV-1", "PCV-2", "PCV Booster",
    "MR", "MR-1", "MR-2", "Measles Rubella", "JE",
    "DPT", "DPT Booster", "Td", "Td-1", "Td-2", "Tetanus",
    "Vitamin A", "Hep B", "Hepatitis B",
    
    # Pregnancy & Maternal Health (Transliterated & Clinical terms)
    "Garbhini", "ANC", "PNC", "Trimester",
    "LMP", "EDD", "Gestational", "Thayi Card",
    "MCP Card", "Anemia", "Hemoglobin", "High Risk Pregnancy",
    "Preeclampsia", "Edema", "Ultrasound", "Fetal Heart Rate",
    "Fetal Movement", "Herige", "Delivery",
    "Colostrum", "Exclusive Breastfeeding",
    
    # Newborn & Infant Health
    "Navajata Shishu", "Birth Weight", "Low Birth Weight",
    "LBW", "Malnutrition", "SAM", "MAM", "Wasting", "Stunting",
    "KMC", "Kangaroo Mother Care", "Jaundice", "Cord Care",
    "Hypothermia", "Dehydration",
    
    # Measurements & Vitals
    "kg", "grams", "cm",
    "BP", "Blood Pressure", "120/80", "110/70", "130/90", "140/90",
    "Pulse", "Temperature", "Fahrenheit", "Celsius", "Weeks", "Months",
    
    # Symptoms & Danger Signs
    "Fever", "Cough", "Cold",
    "Vomiting", "Diarrhea", "Headache",
    "Convulsions", "Fits", "Bleeding", "Swelling",
    "Abdominal Pain", "Shortness of breath", "Chills",
    
    # ASHA / PHC Field Terminology
    "ASHA", "ANM", "Anganwadi",
    "PHC", "CHC", "Sub Center", "VHNSC", "Home Visit",
    "Beneficiary", "Mother", "Infant", "Child", "MCH", "JSSK", "JSY",
    
    # Common Field Medicines
    "IFA", "Iron Folic Acid", "Calcium",
    "Paracetamol", "Albendazole",
    "ORS", "Zinc", "Amoxicillin"
]

# Enforce strict ASCII constraint on keyterms
for term in MEDICAL_KEYTERMS_200:
    assert term.isascii(), f"Non-ASCII character detected in keyterm: '{term}'"
assert len(MEDICAL_KEYTERMS_200) <= 200, f"Keyterm list exceeds 200 limit: {len(MEDICAL_KEYTERMS_200)}"


# Unicode-safe word boundary lookarounds for Indic scripts + alphanumeric text
INDIC_PREFIX = r"(?<![\w\u0C80-\u0CFF\u0900-\u097F])"
INDIC_SUFFIX = r"(?![\w\u0C80-\u0CFF\u0900-\u097F])"

def make_indic_pattern(expr: str) -> str:
    """Wraps an expression with Indic-safe word boundary lookarounds."""
    return f"{INDIC_PREFIX}{expr}{INDIC_SUFFIX}"


# ==============================================================================
# 2. Verified Canonical Normalization & Spelling Variation Mappings
# ==============================================================================
# Maps common ASR phonetics, spelling variations, and spoken abbreviations to
# standardized clinical field terms without altering the speaker's core intent.
VERIFIED_FIND_AND_REPLACE: List[Tuple[str, str]] = [
    # Vaccines (Kannada phonetic / spaced / case variations)
    (make_indic_pattern(r"ಬಿಸಿಜಿ"), "BCG"),
    (make_indic_pattern(r"b\s*c\s*g"), "BCG"),
    (make_indic_pattern(r"bcg\s+vaccine"), "BCG vaccine"),
    (make_indic_pattern(r"ಒಪಿವಿ\s*1"), "OPV-1"),
    (make_indic_pattern(r"ಒಪಿವಿ\s*2"), "OPV-2"),
    (make_indic_pattern(r"ಒಪಿವಿ\s*3"), "OPV-3"),
    (make_indic_pattern(r"ಒಪಿವಿ"), "OPV"),
    (make_indic_pattern(r"o\s*p\s*v"), "OPV"),
    (make_indic_pattern(r"opv\s*1"), "OPV-1"),
    (make_indic_pattern(r"opv\s*2"), "OPV-2"),
    (make_indic_pattern(r"opv\s*3"), "OPV-3"),
    (make_indic_pattern(r"ಪೆಂಟಾ\s*1"), "Penta-1"),
    (make_indic_pattern(r"ಪೆಂಟಾ\s*2"), "Penta-2"),
    (make_indic_pattern(r"ಪೆಂಟಾ\s*3"), "Penta-3"),
    (make_indic_pattern(r"ಪೆಂಟಾವಲೆಂಟ್"), "Pentavalent"),
    (make_indic_pattern(r"ಪೆಂಟಾ"), "Penta"),
    (make_indic_pattern(r"penta\s*1"), "Penta-1"),
    (make_indic_pattern(r"penta\s*2"), "Penta-2"),
    (make_indic_pattern(r"penta\s*3"), "Penta-3"),
    (make_indic_pattern(r"ರೋಟಾ"), "Rota"),
    (make_indic_pattern(r"ರೋಟಾವೈರಸ್"), "Rotavirus"),
    (make_indic_pattern(r"ಐಪಿವಿ"), "IPV"),
    (make_indic_pattern(r"f\s*ipv"), "fIPV"),
    (make_indic_pattern(r"ಪಿಸಿವಿ"), "PCV"),
    (make_indic_pattern(r"ಎಂಆರ್"), "MR"),
    (make_indic_pattern(r"measles\s+rubella"), "MR"),
    (make_indic_pattern(r"ಡಿಪಿಟಿ"), "DPT"),
    (make_indic_pattern(r"ಟಿಟಿ"), "TT"),
    (make_indic_pattern(r"ಟಿಡಿ"), "Td"),
    (make_indic_pattern(r"ವಿಟಮಿನ್\s+ಎ"), "Vitamin A"),
    (make_indic_pattern(r"vitamin\s+a"), "Vitamin A"),

    # Measurements & Units
    (make_indic_pattern(r"ಕೆ\s*\.?\s*ಜಿ"), "kg"),
    (make_indic_pattern(r"k\s*\.?\s*g"), "kg"),
    (make_indic_pattern(r"kilograms?"), "kg"),
    (make_indic_pattern(r"ಕಿಲೋಗ್ರಾಂ"), "kg"),
    (make_indic_pattern(r"ಗ್ರಾಂ"), "grams"),
    (make_indic_pattern(r"ಸೆಂಟಿಮೀಟರ್"), "cm"),
    (make_indic_pattern(r"c\s*m"), "cm"),
    (make_indic_pattern(r"ಬಿ\s*ಪಿ"), "BP"),
    (make_indic_pattern(r"b\s*p"), "BP"),
    (make_indic_pattern(r"120\s+80"), "120/80"),
    (make_indic_pattern(r"120\s+by\s+80"), "120/80"),
    (make_indic_pattern(r"110\s+70"), "110/70"),
    (make_indic_pattern(r"130\s+90"), "130/90"),
    (make_indic_pattern(r"140\s+90"), "140/90"),

    # Field Cards & Programs
    (make_indic_pattern(r"ತಾಯಿ\s+ಕಾರ್ಡ್"), "Thayi Card"),
    (make_indic_pattern(r"thayi\s+card"), "Thayi Card"),
    (make_indic_pattern(r"mcp\s+card"), "MCP Card"),
    (make_indic_pattern(r"ಆಶಾ"), "ASHA"),
    (make_indic_pattern(r"asha\s+worker"), "ASHA worker"),
    (make_indic_pattern(r"ಎಎನ್‌ಎಂ"), "ANM"),
    (make_indic_pattern(r"anm"), "ANM"),
    (make_indic_pattern(r"ಅಂಗನವಾಡಿ"), "Anganwadi"),
    (make_indic_pattern(r"anganwadi"), "Anganwadi"),
    (make_indic_pattern(r"ಪಿಎಚ್‌ಸಿ"), "PHC"),
    (make_indic_pattern(r"phc"), "PHC"),

    # Common Medications
    (make_indic_pattern(r"ಐಎಫ್‌ಎ"), "IFA"),
    (make_indic_pattern(r"ifa\s+tablets?"), "IFA tablets"),
    (make_indic_pattern(r"iron\s+folic\s+acid"), "IFA"),
    (make_indic_pattern(r"ಓಆರ್‌ಎಸ್"), "ORS"),
    (make_indic_pattern(r"ors"), "ORS"),
    (make_indic_pattern(r"ಪ್ಯಾರಸಿಟಮಾಲ್"), "Paracetamol"),
    (make_indic_pattern(r"ಅಲ್ಬೆಂಡಜೋಲ್"), "Albendazole"),
]


# ==============================================================================
# 3. Medical Vocabulary Registry (Metadata & Categorization)
# ==============================================================================
MEDICAL_VOCABULARY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "BCG": {
        "category": "vaccination",
        "kannada": "ಬಿಸಿಜಿ",
        "english": "BCG",
        "description": "Bacillus Calmette-Guerin vaccine given at birth",
        "target_age": "At birth (within 1 year)"
    },
    "OPV": {
        "category": "vaccination",
        "kannada": "ಒಪಿವಿ (ಪೋಲಿಯೊ ಹನಿ)",
        "english": "Oral Polio Vaccine",
        "description": "Polio drops given at birth (0), 6, 10, 14 weeks",
        "target_age": "Birth, 6, 10, 14 weeks"
    },
    "Pentavalent": {
        "category": "vaccination",
        "kannada": "ಪೆಂಟಾವಲೆಂಟ್",
        "english": "Pentavalent Vaccine",
        "description": "5-in-1 vaccine (DPT + Hep B + Hib)",
        "target_age": "6, 10, 14 weeks"
    },
    "Rotavirus": {
        "category": "vaccination",
        "kannada": "ರೋಟಾವೈರಸ್",
        "english": "Rotavirus Vaccine",
        "description": "Oral rotavirus diarrhea prevention drops",
        "target_age": "6, 10, 14 weeks"
    },
    "fIPV": {
        "category": "vaccination",
        "kannada": "ಫ್ರಾಕ್ಷನಲ್ ಐಪಿವಿ",
        "english": "Fractional Inactivated Polio Vaccine",
        "description": "Injectable fractional polio vaccine",
        "target_age": "6, 14 weeks"
    },
    "PCV": {
        "category": "vaccination",
        "kannada": "ಪಿಸಿವಿ",
        "english": "Pneumococcal Conjugate Vaccine",
        "description": "Pneumococcal pneumonia and meningitis vaccine",
        "target_age": "6, 14 weeks, 9 months booster"
    },
    "MR": {
        "category": "vaccination",
        "kannada": "ದಡಾರ ಮತ್ತು ರುಬೆಲ್ಲಾ (ಎಂಆರ್)",
        "english": "Measles-Rubella Vaccine",
        "description": "Measles and Rubella immunization",
        "target_age": "9-12 months, 16-24 months"
    },
    "Vitamin A": {
        "category": "nutrition",
        "kannada": "ವಿಟಮಿನ್ ಎ",
        "english": "Vitamin A",
        "description": "Bi-annual vitamin A supplementation syrup",
        "target_age": "9 months to 5 years"
    },
    "Thayi Card": {
        "category": "program",
        "kannada": "ತಾಯಿ ಕಾರ್ಡ್",
        "english": "Thayi Card",
        "description": "Karnataka Mother and Child Tracking Passport"
    },
    "MCP Card": {
        "category": "program",
        "kannada": "ಎಂಸಿಪಿ ಕಾರ್ಡ್",
        "english": "Mother and Child Protection Card",
        "description": "National MCH registration card"
    },
    "Anemia": {
        "category": "condition",
        "kannada": "ರಕ್ತಹೀನತೆ",
        "english": "Anemia",
        "description": "Low hemoglobin levels (< 11 g/dL in pregnancy)"
    },
    "IFA": {
        "category": "medicine",
        "kannada": "ಐಎಫ್‌ಎ ಮಾತ್ರೆ",
        "english": "Iron and Folic Acid",
        "description": "Daily iron supplementation for pregnant/lactating mothers"
    }
}


def get_formatted_keyterms_header(domain: Optional[str] = None, max_terms: int = 25) -> str:
    """
    Returns comma-separated keyterm prompt string for Gnani Prisma v3.0 header.
    - Strictly ASCII compliant (avoids HTTP header parsing errors).
    - Selects domain-relevant terms (or core 15-20 terms).
    - Caps at max_terms (defaults to 25 for optimal network & API performance).
    """
    domain_clean = domain.lower() if isinstance(domain, str) else None
    if domain_clean and domain_clean in DOMAIN_KEYTERMS_ASCII:
        selected = DOMAIN_KEYTERMS_ASCII[domain_clean]
    elif max_terms >= len(MEDICAL_KEYTERMS_200):
        selected = MEDICAL_KEYTERMS_200
    else:
        selected = CORE_MEDICAL_KEYTERMS_ASCII

    # Clean and filter to strictly ASCII tokens without forbidden characters
    clean_terms: List[str] = []
    for t in selected:
        t_clean = t.strip().replace("<|", "").replace("|>", "")
        if t_clean and t_clean.isascii() and t_clean not in clean_terms:
            clean_terms.append(t_clean)
        if len(clean_terms) >= max_terms:
            break

    return ",".join(clean_terms)
