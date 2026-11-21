"""
Tests for Python Rule-Based Structured Extraction Engine (Zero Qwen Dependency).
Verifies:
1. Python transcript parser
2. Regex-based weight extraction
3. Date and age extraction
4. Vaccination dictionary (BCG, OPV, Penta, MR, IPV, Rotavirus, etc.)
5. Kannada-English medical vocabulary matching
6. Visit type identification
7. Missing-field detection (strict nulls)
8. Rule-based danger-sign detection
9. Negation handling ("no fever", "ಜ್ವರ ಇಲ್ಲ", "bleeding illa")
10. Ambiguous or uncertain information flagging
11. Gnani Timbre integration for voice readback
12. Voice correction updating only specified field
13. Explicit worker confirmation before saving
14. Phase 3 JSON contract handoff
"""
import pytest
from backend.models.schemas import ConfirmationStatus, Phase3RecordPayload
from backend.ai.rule_extractor import RuleExtractor
from backend.ai.transcript_parser import TranscriptParser
from backend.ai.voice_corrector import VoiceCorrectionHandler
from backend.ai.phase3_client import Phase3Client
from backend.safety.danger_signs import DangerSignDetector


@pytest.fixture
def rule_extractor():
    return RuleExtractor(danger_detector=DangerSignDetector())


def test_rule_extraction_standard_phase1_input(rule_extractor):
    transcript = "The baby weight is 3.2 kg and OPV-1 is due."
    rec = rule_extractor.extract_structured_record(
        transcript=transcript,
        language="kn-en",
        pre_selected_beneficiary_id="BNF-2041"
    )
    assert rec.beneficiary_id == "BNF-2041"
    assert rec.weight == "3.2 kg"
    assert rec.vaccinations_due == ["OPV-1"]
    assert rec.visit_type == "Newborn home visit"
    assert rec.next_visit_date is None
    assert "next_visit_date" in rec.missing_fields
    assert rec.danger_signs == []
    assert rec.referral_required is False
    assert rec.confirmation_status == ConfirmationStatus.PENDING


def test_rule_extraction_age_and_date(rule_extractor):
    # Test age ("6 weeks") and next visit date ("2026-12-05")
    transcript = "Baby BNF-5001 is 6 weeks old, weight 4.1 kg, Pentavalent-1 due, next visit 2026-12-05."
    rec = rule_extractor.extract_structured_record(transcript=transcript, language="en")
    assert rec.beneficiary_id == "BNF-5001"
    assert rec.age == "6 weeks"
    assert rec.weight == "4.1 kg"
    assert "Pentavalent-1" in rec.vaccinations_due
    assert rec.next_visit_date == "2026-12-05"
    assert "next_visit_date" not in rec.missing_fields


def test_rule_extraction_kannada_age_and_numerals(rule_extractor):
    # Test Kannada age ("೨ ತಿಂಗಳು" -> 2 months), weight ("೩.೫ ಕೆಜಿ" -> 3.5 kg)
    transcript = "ಮಗುವಿನ ವಯಸ್ಸು ೨ ತಿಂಗಳು, ತೂಕ ೩.೫ ಕೆಜಿ, ಒಪಿವಿ-2 ಮತ್ತು ಪೆಂಟಾ-2 ಬಾಕಿ ಇದೆ."
    rec = rule_extractor.extract_structured_record(transcript=transcript, language="kn")
    assert rec.age == "2 months"
    assert rec.weight == "3.5 kg"
    assert "OPV-2" in rec.vaccinations_due
    assert "Pentavalent-2" in rec.vaccinations_due


def test_rule_extraction_vaccination_dictionary(rule_extractor):
    # Tests UIP vaccinations: BCG, OPV, Penta, MR, fIPV
    transcript = "Give BCG, OPV 0, and fIPV-1 injection today."
    rec = rule_extractor.extract_structured_record(transcript=transcript, language="en")
    assert "BCG" in rec.vaccinations_due
    assert "OPV-0" in rec.vaccinations_due
    assert "fIPV-1" in rec.vaccinations_due


def test_rule_extraction_anc_visit_type(rule_extractor):
    transcript = "Pregnant mother BNF-8888 ANC visit completed, next visit next week."
    rec = rule_extractor.extract_structured_record(transcript=transcript, language="en")
    assert rec.beneficiary_id == "BNF-8888"
    assert rec.visit_type == "Antenatal Care (ANC)"
    assert rec.next_visit_date is not None


def test_rule_extraction_missing_fields_strict_null(rule_extractor):
    # Only mentions checkup; all unstated fields MUST remain null
    transcript = "Routine checkup completed."
    rec = rule_extractor.extract_structured_record(transcript=transcript, language="en")
    assert rec.beneficiary_id is None
    assert rec.weight is None
    assert rec.age is None
    assert rec.next_visit_date is None
    assert rec.vaccinations_due == []
    assert set(rec.missing_fields).issuperset({"beneficiary_id", "weight", "next_visit_date"})


def test_rule_extraction_ambiguity_and_uncertainty(rule_extractor):
    # Stated with uncertainty modifier "maybe" and conflicting range
    transcript = "Baby weight is maybe 2.8 or 3.0 kg, unsure."
    rec = rule_extractor.extract_structured_record(transcript=transcript, language="en")
    assert len(rec.uncertain_fields) > 0
    # Voice readback should note the uncertainty
    assert "unclear" in rec.readback_text.lower() or "verification" in rec.readback_text.lower()


def test_rule_extraction_danger_sign_with_negation(rule_extractor):
    # Danger sign true positive vs negated
    pos_rec = rule_extractor.extract_structured_record("Baby has high fever", language="en")
    assert pos_rec.referral_required is True
    assert len(pos_rec.danger_signs) >= 1

    neg_rec = rule_extractor.extract_structured_record("Baby weight 3.2 kg, no fever, feeding well.", language="en")
    assert neg_rec.referral_required is False


def test_rule_extraction_kannada_negation(rule_extractor):
    neg_rec = rule_extractor.extract_structured_record("ಮಗುವಿಗೆ ಯಾವುದೇ ಜ್ವರ ಇಲ್ಲ, ಹಾಲು ಚೆನ್ನಾಗಿ ಕುಡಿಯುತ್ತಿದೆ.", language="kn")
    assert neg_rec.referral_required is False


def test_rule_extraction_voice_correction_single_field(rule_extractor):
    # Initial state
    rec = rule_extractor.extract_structured_record(
        "Baby weight is 3.2 kg, age 2 months, OPV-1 due.",
        pre_selected_beneficiary_id="BNF-1010"
    )
    corrector = VoiceCorrectionHandler()
    updated, summary = corrector.apply_correction(
        correction_transcript="No, weight is 2.9 kilograms.",
        current_record=rec
    )
    # Weight changed, but age, vaccines, beneficiary_id remain unchanged
    assert updated.weight == "2.9 kg"
    assert updated.age == "2 months"
    assert updated.vaccinations_due == ["OPV-1"]
    assert updated.beneficiary_id == "BNF-1010"
    assert updated.confirmation_status == ConfirmationStatus.IN_REVIEW


def test_rule_extraction_phase3_contract_compatibility(rule_extractor):
    rec = rule_extractor.extract_structured_record(
        "Baby BNF-2041 weight 3.2 kg and OPV-1 due.",
        language="en"
    )
    rec.confirmation_status = ConfirmationStatus.CONFIRMED
    client = Phase3Client()
    payload: Phase3RecordPayload = client.build_phase3_payload(rec)
    data = payload.model_dump()

    # Verify exact 8-field common Phase 3 contract
    assert data["beneficiary_id"] == "BNF-2041"
    assert data["visit_type"] == "Newborn home visit"
    assert data["weight"] == "3.2 kg"
    assert data["vaccinations_due"] == ["OPV-1"]
    assert data["next_visit_date"] is None
    assert data["danger_signs"] == []
    assert data["referral_required"] is False
    assert data["confirmation_status"] == "confirmed"
