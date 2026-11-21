# tests/test_voice_corrector.py
"""
Tests for Voice Correction loop.
Verifies that:
- Verbal corrections update ONLY the relevant field
- Other fields remain intact
- Output is re-validated
- Confirmation status remains pending/in_review until explicit confirmation
"""
import pytest
from backend.models.schemas import ConfirmationStatus


def test_voice_correction_single_field_weight(voice_corrector, sample_pending_record):
    correction = "No, weight is 2.8 kilograms."
    updated, summary = voice_corrector.apply_correction(
        correction_transcript=correction,
        current_record=sample_pending_record,
        language="en"
    )

    # Weight updated to 2.8 kg
    assert updated.weight == "2.8 kg"
    # Beneficiary ID and vaccination must remain INTACT
    assert updated.beneficiary_id == "BNF-2041"
    assert updated.vaccinations_due == ["OPV-1"]
    assert updated.visit_type == "Newborn home visit"
    # Confirmation status remains IN_REVIEW, not confirmed
    assert updated.confirmation_status == ConfirmationStatus.IN_REVIEW
    assert "2.8 kg" in updated.readback_text


def test_voice_correction_vaccination(voice_corrector, sample_pending_record):
    correction = "Vaccine is BCG not OPV-1."
    updated, summary = voice_corrector.apply_correction(
        correction_transcript=correction,
        current_record=sample_pending_record,
        language="en"
    )

    # Vaccination updated to BCG
    assert updated.vaccinations_due == ["BCG"]
    # Weight and Beneficiary ID remain intact
    assert updated.weight == "3.2 kg"
    assert updated.beneficiary_id == "BNF-2041"
    assert updated.confirmation_status != ConfirmationStatus.CONFIRMED


def test_voice_correction_next_visit_date(voice_corrector, sample_pending_record):
    correction = "Next visit date is 2026-11-28."
    updated, summary = voice_corrector.apply_correction(
        correction_transcript=correction,
        current_record=sample_pending_record,
        language="en"
    )

    assert updated.next_visit_date == "2026-11-28"
    assert "next_visit_date" not in updated.missing_fields
    assert updated.weight == "3.2 kg"


def test_voice_correction_kannada(voice_corrector, sample_pending_record):
    correction = "ತೂಕ 2.8 ಕೆಜಿ"
    updated, summary = voice_corrector.apply_correction(
        correction_transcript=correction,
        current_record=sample_pending_record,
        language="kn"
    )

    assert updated.weight == "2.8 kg"
    assert updated.beneficiary_id == "BNF-2041"
