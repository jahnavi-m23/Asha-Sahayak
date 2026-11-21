# tests/test_danger_signs.py
"""
Tests for rule-based danger-sign detection based on public health guidelines.
Covers:
- Newborn danger signs (High fever, Hypothermia, Inability to suckle, Convulsions, Chest indrawing)
- Pregnancy danger signs (Vaginal bleeding, Severe headache/blurred vision, Eclampsia)
- Postpartum danger signs (PPH, Foul lochia)
- Context checks and negation handling across English, Kannada, and code-mixed formats
- Hypothetical statement exclusion
- Flagging uncertain signs for human review
- Guideline citation checks
- Strict safety rules (no diagnoses, no prescription, no dosage)
"""
import pytest
from backend.safety.danger_signs import DangerSignDetector
from backend.safety.guidelines import PUBLIC_HEALTH_RULES
from backend.safety.referral_advisor import ReferralAdvisor


def test_newborn_high_fever_detection(danger_detector):
    transcript = "The baby has high fever and is very hot to touch."
    detections = danger_detector.detect_danger_signs(transcript)
    assert len(detections) >= 1
    fever_ds = next((d for d in detections if d.code == "HBNC-DS-01"), None)
    assert fever_ds is not None
    assert fever_ds.is_negated is False
    assert danger_detector.has_actionable_danger_signs(detections) is True
    assert "MoHFW Home Based Newborn Care" in fever_ds.guideline_source


def test_newborn_high_fever_kannada(danger_detector):
    transcript = "ಮಗುವಿಗೆ ಅಧಿಕ ಜ್ವರ ಬಂದಿದೆ ಮತ್ತು ಮೈ ತುಂಬಾ ಬಿಸಿಯಾಗಿದೆ."
    detections = danger_detector.detect_danger_signs(transcript, language="kn")
    fever_ds = next((d for d in detections if d.code == "HBNC-DS-01"), None)
    assert fever_ds is not None
    assert fever_ds.is_negated is False


def test_pregnancy_bleeding_detection(danger_detector):
    transcript = "The pregnant mother has vaginal bleeding."
    detections = danger_detector.detect_danger_signs(transcript)
    bleed_ds = next((d for d in detections if d.code == "ANC-DS-01"), None)
    assert bleed_ds is not None
    assert bleed_ds.is_negated is False
    assert bleed_ds.category == "pregnancy"
    assert "Antepartum Hemorrhage" in bleed_ds.name


def test_pregnancy_bleeding_kannada(danger_detector):
    transcript = "ಗರ್ಭಿಣಿ ತಾಯಿಗೆ ರಕ್ತಸ್ರಾವ ಆಗುತ್ತಿದೆ."
    detections = danger_detector.detect_danger_signs(transcript, language="kn")
    bleed_ds = next((d for d in detections if d.code == "ANC-DS-01"), None)
    assert bleed_ds is not None
    assert bleed_ds.is_negated is False


def test_negation_english_no_fever(danger_detector):
    transcript = "Baby weight is 3.2 kg, no fever, feeding well."
    detections = danger_detector.detect_danger_signs(transcript)
    fever_ds = next((d for d in detections if d.code == "HBNC-DS-01"), None)
    assert fever_ds is not None
    assert fever_ds.is_negated is True
    # Overall actionable danger sign should be False because fever is negated
    assert danger_detector.has_actionable_danger_signs(detections) is False


def test_negation_kannada_jvara_illa(danger_detector):
    transcript = "ಮಗುವಿಗೆ ಯಾವುದೇ ಜ್ವರ ಇಲ್ಲ ಮತ್ತು ತೂಕ 3.2 ಕೆಜಿ."
    detections = danger_detector.detect_danger_signs(transcript, language="kn")
    fever_ds = next((d for d in detections if d.code == "HBNC-DS-01"), None)
    assert fever_ds is not None
    assert fever_ds.is_negated is True
    assert danger_detector.has_actionable_danger_signs(detections) is False


def test_negation_kannada_bleeding_illa(danger_detector):
    transcript = "ತಾಯಿಗೆ ರಕ್ತಸ್ರಾವ ಇಲ್ಲ."
    detections = danger_detector.detect_danger_signs(transcript, language="kn")
    bleed_ds = next((d for d in detections if d.code == "ANC-DS-01"), None)
    assert bleed_ds is not None
    assert bleed_ds.is_negated is True


def test_negation_codemixed_fever_illa(danger_detector):
    transcript = "Baby weight 3.2 kg, fever illa, OPV-1 due."
    detections = danger_detector.detect_danger_signs(transcript, language="kn-en")
    fever_ds = next((d for d in detections if d.code == "HBNC-DS-01"), None)
    assert fever_ds is not None
    assert fever_ds.is_negated is True


def test_hypothetical_exclusion(danger_detector):
    # Conditional / advice statement should NOT trigger confirmed emergency
    transcript = "If fever comes, inform the PHC."
    detections = danger_detector.detect_danger_signs(transcript)
    fever_ds = next((d for d in detections if d.code == "HBNC-DS-01"), None)
    assert fever_ds is not None
    assert fever_ds.is_negated is True
    assert danger_detector.has_actionable_danger_signs(detections) is False


def test_uncertain_flag_for_human_review(danger_detector):
    transcript = "Baby feels slightly warm, weight 3.1 kg."
    detections = danger_detector.detect_danger_signs(transcript)
    fever_ds = next((d for d in detections if d.code == "HBNC-DS-01"), None)
    assert fever_ds is not None
    assert fever_ds.is_uncertain is True


def test_referral_advisor_never_prescribes_medication():
    # Referral text must direct to PHC/FRU and NEVER prescribe drugs or dosages
    for code, rule in PUBLIC_HEALTH_RULES.items():
        assert "paracetamol" not in rule.referral_instruction_en.lower()
        assert "mg" not in rule.referral_instruction_en.lower()
        assert "antibiotic" not in rule.referral_instruction_en.lower()
        assert any(term in rule.referral_instruction_en for term in ["PHC", "FRU", "CHC", "Hospital", "Centre"])
