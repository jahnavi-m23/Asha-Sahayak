# backend/safety/guidelines.py
"""
Public Health Guidelines and Danger Sign Rules.
Based on standard public health guidelines approved for ASHA workers:
1. MoHFW Home Based Newborn Care (HBNC) Operational Guidelines (Govt of India).
2. WHO / UNICEF Integrated Management of Neonatal and Childhood Illness (IMNCI).
3. MoHFW Guidelines for Antenatal Care (ANC) and Skilled Attendance at Birth.

SAFETY RULES:
- Never diagnose, prescribe treatment, or recommend drug dosage.
- Direct to nearest Primary Health Centre (PHC), Community Health Centre (CHC), or First Referral Unit (FRU).
- Every rule documents its public health source citation.
"""
from typing import List, Dict
from dataclasses import dataclass, field
from backend.models.schemas import DangerSignSeverity


@dataclass
class DangerSignRule:
    """Predefined rule for danger sign detection."""
    code: str
    name_en: str
    name_kn: str
    category: str  # "newborn", "pregnancy", "postpartum", "child"
    severity: DangerSignSeverity
    guideline_source: str
    keywords_en: List[str]
    keywords_kn: List[str]
    referral_instruction_en: str
    referral_instruction_kn: str
    uncertain_keywords: List[str] = field(default_factory=list)


PUBLIC_HEALTH_RULES: Dict[str, DangerSignRule] = {
    # -------------------------------------------------------------
    # 1. NEWBORN DANGER SIGNS (MoHFW HBNC & IMNCI Guidelines)
    # -------------------------------------------------------------
    "HBNC-DS-01": DangerSignRule(
        code="HBNC-DS-01",
        name_en="High fever in newborn (> 38°C / 100.4°F)",
        name_kn="ನವಜಾತ ಶಿಶುವಿನಲ್ಲಿ ಅಧಿಕ ಜ್ವರ",
        category="newborn",
        severity=DangerSignSeverity.CRITICAL_EMERGENCY,
        guideline_source=(
            "MoHFW Home Based Newborn Care (HBNC) Operational Guidelines (Govt of India) "
            "& WHO/UNICEF IMNCI - Section: Serious Neonatal Illness"
        ),
        keywords_en=[
            "high fever", "fever", "very hot", "high temperature",
            "burning fever", "pyrexia", "hot to touch"
        ],
        keywords_kn=[
            "ಜ್ವರ", "ಅಧಿಕ ಜ್ವರ", "ತುಂಬಾ ಜ್ವರ", "ಮೈ ಬಿಸಿ", "ತೀವ್ರ ಜ್ವರ"
        ],
        referral_instruction_en=(
            "URGENT: High fever detected in newborn. Keep baby warm and refer immediately "
            "to the nearest Primary Health Centre (PHC) or Community Health Centre (CHC). "
            "Do not administer adult medications."
        ),
        referral_instruction_kn=(
            "ತುರ್ತು: ನವಜಾತ ಶಿಶುವಿನಲ್ಲಿ ಅಧಿಕ ಜ್ವರ ಕಂಡುಬಂದಿದೆ. ಮಗುವನ್ನು ಬೆಚ್ಚಗಿರಿಸಿ ಮತ್ತು ತಕ್ಷಣವೇ "
            "ಹತ್ತಿರದ ಪ್ರಾಥಮಿಕ ಆರೋಗ್ಯ ಕೇಂದ್ರ (PHC) ಅಥವಾ CHC ಗೆ ಕರೆದೊಯ್ಯಿರಿ. ಔಷಧ ನೀಡಬೇಡಿ."
        ),
        uncertain_keywords=["slightly warm", "mild warmth", "ಸ್ವಲ್ಪ ಬಿಸಿ"]
    ),

    "HBNC-DS-02": DangerSignRule(
        code="HBNC-DS-02",
        name_en="Hypothermia / Cold to touch (< 35.5°C)",
        name_kn="ಮಗು ಅತಿಯಾಗಿ ತಣ್ಣಗಾಗುವುದು (ಹೈಪೋಥರ್ಮಿಯಾ)",
        category="newborn",
        severity=DangerSignSeverity.CRITICAL_EMERGENCY,
        guideline_source="MoHFW HBNC Module 3: Danger Signs Assessment in Newborns",
        keywords_en=[
            "hypothermia", "cold to touch", "body is cold", "baby is cold",
            "cold extremities", "shivering baby", "freezing cold"
        ],
        keywords_kn=[
            "ಮಗು ತಣ್ಣಗಾಗಿದೆ", "ಮೈ ತಣ್ಣಗಾಗಿದೆ", "ಅತಿಯಾಗಿ ತಣ್ಣಗಾಗಿದೆ", "ತಣ್ಣಗೆ"
        ],
        referral_instruction_en=(
            "URGENT: Hypothermia detected. Provide immediate Kangaroo Mother Care (skin-to-skin "
            "contact) and transport urgently to the nearest PHC/FRU."
        ),
        referral_instruction_kn=(
            "ತುರ್ತು: ಮಗು ಅತಿಯಾಗಿ ತಣ್ಣಗಾಗಿದೆ. ತಕ್ಷಣ ಕಾಂಗರೂ ತಾಯಿ ಆರೈಕೆ (ಚರ್ಮಕ್ಕೆ ಚರ್ಮದ ಸ್ಪರ್ಶ) "
            "ನೀಡಿ ತಕ್ಷಣ PHC/FRU ಗೆ ಕರೆದೊಯ್ಯಿರಿ."
        )
    ),

    "HBNC-DS-03": DangerSignRule(
        code="HBNC-DS-03",
        name_en="Inability to feed or suckle at breast",
        name_kn="ಹಾಲು ಕುಡಿಯಲು ಅಸಮರ್ಥತೆ / ಎದೆಹಾಲು ಹೀರುತ್ತಿಲ್ಲ",
        category="newborn",
        severity=DangerSignSeverity.CRITICAL_EMERGENCY,
        guideline_source="WHO/UNICEF IMNCI Young Infant Clinical Protocols",
        keywords_en=[
            "unable to feed", "cannot suck", "stopped suckling", "not sucking",
            "unable to drink", "vomits everything", "not drinking milk"
        ],
        keywords_kn=[
            "ಹಾಲು ಕುಡಿಯುತ್ತಿಲ್ಲ", "ಎದೆಹಾಲು ಹೀರುತ್ತಿಲ್ಲ", "ಹಾಲು ಕುಡಿಯಲು ಸಾಧ್ಯವಿಲ್ಲ",
            "ಹಾಲು ಕುಡಿಯೋದು ನಿಲ್ಲಿಸಿದೆ"
        ],
        referral_instruction_en=(
            "URGENT: Baby unable to feed at breast. This is a critical danger sign of severe "
            "illness. Facilitate emergency transport to the nearest PHC/FRU immediately."
        ),
        referral_instruction_kn=(
            "ತುರ್ತು: ಮಗುವಿಗೆ ಎದೆಹಾಲು ಕುಡಿಯಲು ಆಗುತ್ತಿಲ್ಲ. ತಕ್ಷಣವೇ ತುರ್ತು ವಾಹನದ ಮೂಲಕ PHC ಅಥವಾ FRU ಗೆ "
            "ದಾಖಲಿಸಿ."
        )
    ),

    "HBNC-DS-04": DangerSignRule(
        code="HBNC-DS-04",
        name_en="Convulsions / Fits / Abnormal movements",
        name_kn="ಫಿಟ್ಸ್ / ಸೆಳವು / ನಡುಕ",
        category="newborn",
        severity=DangerSignSeverity.CRITICAL_EMERGENCY,
        guideline_source="MoHFW HBNC Manual & IMNCI Guidelines for Sick Young Infant",
        keywords_en=[
            "convulsions", "fits", "seizures", "jerking", "twitching",
            "spasms", "abnormal movements", "shaking violently"
        ],
        keywords_kn=[
            "ಫಿಟ್ಸ್", "ಸೆಳವು", "ನಡುಕ", "ಕೈಕಾಲು ಸೆಳೆಯುವುದು", "ಮೂರ್ಛೆ"
        ],
        referral_instruction_en=(
            "CRITICAL EMERGENCY: Convulsions detected in newborn. Keep airway clear, "
            "do not put anything in mouth, and rush immediately to the nearest First Referral Unit (FRU) / District Hospital."
        ),
        referral_instruction_kn=(
            "ಅತ್ಯಂತ ತುರ್ತು: ಶಿಶುವಿನಲ್ಲಿ ಫಿಟ್ಸ್/ಸೆಳವು ಕಂಡುಬಂದಿದೆ. ಬಾಯಿಯಲ್ಲಿ ಏನನ್ನೂ ಹಾಕಬೇಡಿ, "
            "ತಕ್ಷಣವೇ ಪ್ರಥಮ ಶಿಫಾರಸು ಘಟಕ (FRU) ಅಥವಾ ಜಿಲ್ಲಾ ಆಸ್ಪತ್ರೆಗೆ ಕರೆದೊಯ್ಯಿರಿ."
        )
    ),

    "HBNC-DS-05": DangerSignRule(
        code="HBNC-DS-05",
        name_en="Fast breathing / Severe chest indrawing",
        name_kn="ವೇಗವಾಗಿ ಉಸಿರಾಡುವುದು / ಎದೆ ಒಳಗೆ ಎಳೆಯುವುದು",
        category="newborn",
        severity=DangerSignSeverity.CRITICAL_EMERGENCY,
        guideline_source="MoHFW HBNC Operational Guidelines: Respiratory Distress Management",
        keywords_en=[
            "fast breathing", "rapid breathing", "chest indrawing", "difficulty breathing",
            "shortness of breath", "grunting", "gasping"
        ],
        keywords_kn=[
            "ವೇಗದ ಉಸಿರಾಟ", "ಉಸಿರಾಟದ ತೊಂದರೆ", "ಎದೆ ಒಳಗೆ ಎಳೆಯುತ್ತಿದೆ", "ಉಸಿರು ಕಟ್ಟುತ್ತಿದೆ"
        ],
        referral_instruction_en=(
            "URGENT: Respiratory distress / severe chest indrawing detected. Keep airway clear and "
            "refer immediately to the nearest PHC/CHC equipped with oxygen support."
        ),
        referral_instruction_kn=(
            "ತುರ್ತು: ಮಗುವಿನಲ್ಲಿ ತೀವ್ರ ಉಸಿರಾಟದ ತೊಂದರೆ ಕಂಡುಬಂದಿದೆ. ತಕ್ಷಣ ಆಮ್ಲಜನಕ ಸೌಲಭ್ಯವಿರುವ "
            "ಹತ್ತಿರದ PHC ಅಥವಾ CHC ಗೆ ಕರೆದೊಯ್ಯಿರಿ."
        )
    ),

    "HBNC-DS-06": DangerSignRule(
        code="HBNC-DS-06",
        name_en="Severe Jaundice (Day 1 or Palms/Soles yellow)",
        name_kn="ತೀವ್ರ ಕಾಮಾಲೆ (ಹಳದಿ ಬಣ್ಣ)",
        category="newborn",
        severity=DangerSignSeverity.HIGH,
        guideline_source="MoHFW HBNC Guidelines: Protocol for Neonatal Jaundice",
        keywords_en=[
            "severe jaundice", "jaundice", "yellow palms", "yellow soles",
            "yellow eyes", "yellow skin day 1", "deep yellow"
        ],
        keywords_kn=[
            "ಕಾಮಾಲೆ", "ಹಳದಿ ಕಣ್ಣು", "ಮೈ ಹಳದಿ", "ತೀವ್ರ ಕಾಮಾಲೆ"
        ],
        referral_instruction_en=(
            "HIGH PRIORITY: Severe jaundice detected. Refer to Primary Health Centre for phototherapy "
            "assessment and serum bilirubin testing."
        ),
        referral_instruction_kn=(
            "ಪ್ರಮುಖ: ತೀವ್ರ ಕಾಮಾಲೆ ಕಂಡುಬಂದಿದೆ. ಫೋಟೊಥೆರಪಿ ಮತ್ತು ತಪಾಸಣೆಗಾಗಿ ತಕ್ಷಣ PHC ಗೆ ಕರೆದೊಯ್ಯಿರಿ."
        ),
        uncertain_keywords=["slight yellow", "mild yellow", "ಸ್ವಲ್ಪ ಹಳದಿ"]
    ),

    "HBNC-DS-07": DangerSignRule(
        code="HBNC-DS-07",
        name_en="Umbilical cord infection (Pus discharge / Redness)",
        name_kn="ಹೊಕ್ಕುಳ ಬಳ್ಳಿ ಸೋಂಕು (ಕೀವು / ಕೆಂಪಾಗುವುದು)",
        category="newborn",
        severity=DangerSignSeverity.HIGH,
        guideline_source="MoHFW HBNC Manual: Cord Care and Umbilical Sepsis Management",
        keywords_en=[
            "pus from cord", "umbilical pus", "cord bleeding", "cord infection",
            "redness around cord", "foul smelling cord"
        ],
        keywords_kn=[
            "ಹೊಕ್ಕುಳಿನಲ್ಲಿ ಕೀವು", "ಹೊಕ್ಕುಳು ಕೆಂಪಾಗಿದೆ", "ಹೊಕ್ಕುಳಿನ ಸೋಂಕು", "ವಾಸನೆ ಬರುತ್ತಿದೆ"
        ],
        referral_instruction_en=(
            "HIGH PRIORITY: Umbilical sepsis/pus detected. Keep the cord clean and dry; do not apply "
            "home remedies. Refer immediately to PHC for medical evaluation."
        ),
        referral_instruction_kn=(
            "ಪ್ರಮುಖ: ಹೊಕ್ಕುಳ ಬಳ್ಳಿಯಲ್ಲಿ ಕೀವು ಕಂಡುಬಂದಿದೆ. ಯಾವುದೇ ಕ್ರೀಮ್ ಅಥವಾ ಪುಡಿ ಹಚ್ಚಬೇಡಿ, ತಕ್ಷಣ PHC ಗೆ ಭೇಟಿ ನೀಡಿ."
        )
    ),

    # -------------------------------------------------------------
    # 2. PREGNANCY DANGER SIGNS (MoHFW ANC Guidelines)
    # -------------------------------------------------------------
    "ANC-DS-01": DangerSignRule(
        code="ANC-DS-01",
        name_en="Vaginal bleeding during pregnancy (Antepartum Hemorrhage)",
        name_kn="ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಯೋನಿ ರಕ್ತಸ್ರಾವ",
        category="pregnancy",
        severity=DangerSignSeverity.CRITICAL_EMERGENCY,
        guideline_source=(
            "MoHFW Guidelines for Antenatal Care and Skilled Attendance at Birth (Govt of India) "
            "- Section: Identification and Management of Obstetric Complications"
        ),
        keywords_en=[
            "bleeding during pregnancy", "vaginal bleeding", "bleeding per vaginum",
            "antepartum hemorrhage", "spotting blood", "heavy bleeding", "blood discharge"
        ],
        keywords_kn=[
            "ರಕ್ತಸ್ರಾವ", "ಯೋನಿ ರಕ್ತಸ್ರಾವ", "ರಕ್ತ ಹೋಗುತ್ತಿದೆ", "ರಕ್ತಸ್ರಾವವಾಗುತ್ತಿದೆ", "ರಕ್ತ ಬೀಳುತ್ತಿದೆ"
        ],
        referral_instruction_en=(
            "CRITICAL EMERGENCY: Bleeding during pregnancy detected. Patient must rest lying down. "
            "Arrange immediate emergency transport (108 Ambulance) to the nearest First Referral Unit (FRU)."
        ),
        referral_instruction_kn=(
            "ಅತ್ಯಂತ ತುರ್ತು: ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ರಕ್ತಸ್ರಾವ ಕಂಡುಬಂದಿದೆ. ತಕ್ಷಣ 108 ಆಂಬುಲೆನ್ಸ್ ಕರೆಸಿ "
            "ಹತ್ತಿರದ ಪ್ರಥಮ ಶಿಫಾರಸು ಘಟಕ (FRU) ಅಥವಾ ಜಿಲ್ಲಾ ಆಸ್ಪತ್ರೆಗೆ ದಾಖಲಿಸಿ."
        )
    ),

    "ANC-DS-02": DangerSignRule(
        code="ANC-DS-02",
        name_en="Severe headache with blurred vision / High BP (Pre-eclampsia)",
        name_kn="ತೀವ್ರ ತಲೆನೋವು, ಕಣ್ಣು ಮಸುಕಾಗುವುದು ಮತ್ತು ಅಧಿಕ ರಕ್ತದೊತ್ತಡ",
        category="pregnancy",
        severity=DangerSignSeverity.CRITICAL_EMERGENCY,
        guideline_source="MoHFW ANC Guidelines: Detection and Triage of Severe Pre-eclampsia",
        keywords_en=[
            "severe headache", "blurred vision", "high blood pressure", "high bp",
            "epigastric pain", "swelling in face and hands", "pre-eclampsia"
        ],
        keywords_kn=[
            "ತೀವ್ರ ತಲೆನೋವು", "ಕಣ್ಣು ಮಸುಕು", "ಹೆಚ್ಚು ಬಿಪಿ", "ಮುಖ ಊದಿಕೊಂಡಿದೆ", "ಕೈಕಾಲು ಊತ"
        ],
        referral_instruction_en=(
            "CRITICAL EMERGENCY: Severe headache with blurred vision indicates possible severe pre-eclampsia. "
            "Refer immediately to FRU/CHC for blood pressure management and monitoring."
        ),
        referral_instruction_kn=(
            "ಅತ್ಯಂತ ತುರ್ತು: ತೀವ್ರ ತಲೆನೋವು ಮತ್ತು ಕಣ್ಣು ಮಸುಕಾಗುವುದು ಪ್ರಿ-ಎಕ್ಲಾಂಪ್ಸಿಯಾದ ಲಕ್ಷಣವಾಗಿರಬಹುದು. "
            "ತಕ್ಷಣ FRU/CHC ಆಸ್ಪತ್ರೆಗೆ ದಾಖಲಿಸಿ."
        )
    ),

    "ANC-DS-03": DangerSignRule(
        code="ANC-DS-03",
        name_en="Convulsions / Fits during pregnancy (Eclampsia)",
        name_kn="ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಫಿಟ್ಸ್ / ಸೆಳವು (ಎಕ್ಲಾಂಪ್ಸಿಯಾ)",
        category="pregnancy",
        severity=DangerSignSeverity.CRITICAL_EMERGENCY,
        guideline_source="MoHFW Guidelines for Emergency Obstetric Care (EmOC)",
        keywords_en=[
            "fits in pregnancy", "eclampsia", "seizures in pregnancy", "pregnant woman convulsions"
        ],
        keywords_kn=[
            "ಗರ್ಭಿಣಿಗೆ ಫಿಟ್ಸ್", "ಗರ್ಭಿಣಿಗೆ ಸೆಳವು", "ಗರ್ಭಿಣಿ ಮೂರ್ಛೆ"
        ],
        referral_instruction_en=(
            "CRITICAL OBSTETRIC EMERGENCY: Eclampsia detected. Turn patient to left lateral position, "
            "keep airway clear, and rush immediately to First Referral Unit (FRU)."
        ),
        referral_instruction_kn=(
            "ಅತ್ಯಂತ ತುರ್ತು: ಗರ್ಭಿಣಿಗೆ ಫಿಟ್ಸ್ ಕಂಡುಬಂದಿದೆ. ಎಡ ಮಗ್ಗಲಿಗೆ ಮಲಗಿಸಿ ತಕ್ಷಣವೇ 108 ಆಂಬುಲೆನ್ಸ್ ಮೂಲಕ "
            "FRU ಗೆ ಕರೆದೊಯ್ಯಿರಿ."
        )
    ),

    # -------------------------------------------------------------
    # 3. POSTPARTUM DANGER SIGNS (MoHFW PNC Guidelines)
    # -------------------------------------------------------------
    "PNC-DS-01": DangerSignRule(
        code="PNC-DS-01",
        name_en="Severe postpartum bleeding (Postpartum Hemorrhage - PPH)",
        name_kn="ಹೆರಿಗೆಯ ನಂತರ ಅತಿಯಾದ ರಕ್ತಸ್ರಾವ",
        category="postpartum",
        severity=DangerSignSeverity.CRITICAL_EMERGENCY,
        guideline_source="MoHFW Guidelines for Postnatal Care and Management of PPH",
        keywords_en=[
            "postpartum hemorrhage", "pph", "excessive bleeding after delivery",
            "severe bleeding after delivery", "soaking pads quickly", "bleeding profusely"
        ],
        keywords_kn=[
            "ಹೆರಿಗೆಯ ನಂತರ ರಕ್ತಸ್ರಾವ", "ಅತಿಯಾದ ರಕ್ತಸ್ರಾವ", "ತುಂಬಾ ರಕ್ತ ಹೋಗುತ್ತಿದೆ"
        ],
        referral_instruction_en=(
            "CRITICAL EMERGENCY: Severe postpartum hemorrhage (PPH) detected. Massage uterus, "
            "keep warm, and transport urgently to FRU."
        ),
        referral_instruction_kn=(
            "ಅತ್ಯಂತ ತುರ್ತು: ಹೆರಿಗೆಯ ನಂತರ ಅತಿಯಾದ ರಕ್ತಸ್ರಾವ ಕಂಡುಬಂದಿದೆ. ತಕ್ಷಣ 108 ಆಂಬುಲೆನ್ಸ್ ಮೂಲಕ FRU ಗೆ ಕರೆದೊಯ್ಯಿರಿ."
        )
    ),

    "PNC-DS-02": DangerSignRule(
        code="PNC-DS-02",
        name_en="Foul-smelling vaginal discharge / Puerperal sepsis",
        name_kn="ವಾಸನೆಯುಕ್ತ ಸ್ರಾವ / ಹೆರಿಗೆಯ ನಂತರದ ಸೋಂಕು",
        category="postpartum",
        severity=DangerSignSeverity.HIGH,
        guideline_source="MoHFW Postnatal Care Manual: Prevention and Detection of Puerperal Sepsis",
        keywords_en=[
            "foul smelling lochia", "foul smelling discharge", "bad odor discharge",
            "puerperal sepsis", "severe lower abdominal pain after delivery"
        ],
        keywords_kn=[
            "ವಾಸನೆಯುಕ್ತ ಸ್ರಾವ", "ವಾಸನೆ ಬರುತ್ತಿದೆ", "ಕೆಳಹೊಟ್ಟೆ ನೋವು"
        ],
        referral_instruction_en=(
            "HIGH PRIORITY: Foul-smelling lochia/discharge detected. Requires urgent assessment "
            "for puerperal sepsis at Primary Health Centre."
        ),
        referral_instruction_kn=(
            "ಪ್ರಮುಖ: ಹೆರಿಗೆಯ ನಂತರ ದುರ್ವಾಸನೆಯ ಸ್ರಾವ ಕಂಡುಬಂದಿದೆ. ತಕ್ಷಣವೇ PHC ಗೆ ಕರೆದೊಯ್ದು ತಪಾಸಣೆ ಮಾಡಿಸಿ."
        )
    )
}
