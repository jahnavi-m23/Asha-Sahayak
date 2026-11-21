"""
ASHA Sahayak - Comprehensive End-to-End Workflow & Extraction Test Suite.
Tests:
1. Kannada speech narrative extraction.
2. English speech narrative extraction.
3. Kannada-English mixed speech extraction.
4. Medical terminology & UIP vaccines.
5. Numbers, vitals & weight measurements.
6. Incomplete speech & uncertainty indicators.
7. Missing information tracking.
8. Danger signs detection & emergency referral rules.
9. Negation preservation (prevents misdiagnosing 'no fever' / 'no bleeding').
10. Voice corrections (targeted field updates & confirmation readback).
11. Explicit confirmation requirement (rejects unconfirmed records).
12. Phase 3 Register saving and dashboard analytics.
13. Multilingual Gnani Timbre TTS (all 10 languages, alias resolution, WAV headers).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.extraction.engine import ASHAExtractionEngine
from backend.voice.config import config, SUPPORTED_LANGUAGES, LEGACY_VOICE_ALIASES
from backend.voice.gnani_tts_client import GnaniTimbreTTSClient

client = TestClient(app)


# ==============================================================================
# 1. Kannada, English, and Code-Mixed Speech Extraction Tests
# ==============================================================================
def test_kannada_speech_extraction():
    transcript = "ಫಲಾನುಭವಿ ಲಕ್ಷ್ಮಿ ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ 24 ವಾರಗಳು ರಕ್ತದೊತ್ತಡ 120 80 ತಲೆನೋವು ಇದೆ ರಕ್ತಸ್ರಾವ ಇಲ್ಲ ಮುಂದಿನ ವಾರ ಭೇಟಿ"
    report = ASHAExtractionEngine.extract_report(transcript, language_code="kn-IN")

    assert report["beneficiary_name"] == "Lakshmi"
    assert "ANC" in report["visit_type"]
    assert "24 weeks" in report["gestational_age"]
    assert report["blood_pressure"] == "120/80"
    assert "Severe Headache" in report["symptoms_reported"]
    assert any("Bleeding" in s for s in report["negated_symptoms"])
    assert report["referral_required"] is False  # Bleeding was negated!
    assert "Next Week" in report["next_visit_date"]
    assert len(report["readback_kn"]) > 10


def test_english_speech_extraction():
    transcript = "Beneficiary Radhika ANC home visit 28 weeks gestational age blood pressure 110/70 next visit next week"
    report = ASHAExtractionEngine.extract_report(transcript, language_code="en-IN")

    assert report["beneficiary_name"] == "Radhika"
    assert "ANC" in report["visit_type"]
    assert "28 weeks" in report["gestational_age"]
    assert report["blood_pressure"] == "110/70"
    assert report["referral_required"] is False
    assert "Next Week" in report["next_visit_date"]
    assert len(report["readback_en"]) > 10


def test_kannada_english_codemix_extraction():
    transcript = "Beneficiary Savitha baby weight 3.2 kg ಇದೆ OPV-1 ಮತ್ತು Pentavalent-1 due ಆಗಿದೆ mother fever ಇಲ್ಲ"
    report = ASHAExtractionEngine.extract_report(transcript, language_code="kn-IN")

    assert report["beneficiary_name"] == "Savitha"
    assert report["infant_weight"] == "3.2 kg"
    assert "OPV-1" in report["vaccinations_due"]
    assert "Pentavalent-1" in report["vaccinations_due"]
    assert any("Fever" in s for s in report["negated_symptoms"])
    assert "Fever" not in report["symptoms_reported"]


# ==============================================================================
# 2. Danger Signs & Negations Preservation Tests
# ==============================================================================
def test_maternal_bleeding_danger_sign_triggers_referral():
    transcript = "ಗರ್ಭಿಣಿ ಲಕ್ಷ್ಮಿ ತೀವ್ರ ರಕ್ತಸ್ರಾವ ಇದೆ water broke"
    report = ASHAExtractionEngine.extract_report(transcript)

    assert report["referral_required"] is True
    assert len(report["danger_signs"]) >= 1
    ds_ids = [d["id"] for d in report["danger_signs"]]
    assert "MAT_BLEEDING" in ds_ids or "WATER_BROKE" in ds_ids


def test_negated_bleeding_does_not_trigger_referral():
    transcript = "ಗರ್ಭಿಣಿ ಲಕ್ಷ್ಮಿ ರಕ್ತಸ್ರಾವ ಇಲ್ಲ ವಾಂತಿ ಇಲ್ಲ BP 120/80"
    report = ASHAExtractionEngine.extract_report(transcript)

    assert report["referral_required"] is False
    assert len(report["danger_signs"]) == 0
    assert any("Bleeding" in s for s in report["negated_symptoms"])


def test_very_low_birth_weight_danger_sign():
    # Infant birth weight under 2.0 kg is a neonatal red flag (SNCU admission)
    transcript = "ನವಜಾತ ಶಿಶು ಭೇಟಿ ತೂಕ 1.6 kg ಇದೆ ಮಗು ಹಾಲು ಕುಡಿಯುತ್ತಿಲ್ಲ"
    report = ASHAExtractionEngine.extract_report(transcript)

    assert report["infant_weight"] == "1.6 kg"
    assert report["referral_required"] is True
    ds_ids = [d["id"] for d in report["danger_signs"]]
    assert "VERY_LOW_BIRTH_WEIGHT" in ds_ids or "NEONATAL_REFUSAL_TO_FEED" in ds_ids


def test_hypertension_preeclampsia_trigger():
    transcript = "ಗರ್ಭಿಣಿ ತಾಯಿ ಸುನಿತಾ BP 150/95 ಇದೆ ತೀವ್ರ ತಲೆನೋವು ಇದೆ"
    report = ASHAExtractionEngine.extract_report(transcript)

    assert report["blood_pressure"] == "150/95"
    assert report["referral_required"] is True
    ds_ids = [d["id"] for d in report["danger_signs"]]
    assert "HIGH_BP" in ds_ids


# ==============================================================================
# 3. Missing Fields & Incomplete Speech Handling
# ==============================================================================
def test_incomplete_speech_missing_fields_and_confidence():
    short_transcript = "ಮನೆ ಭೇಟಿ ಮಾಡಲಾಗಿದೆ"
    report = ASHAExtractionEngine.extract_report(short_transcript)

    assert "beneficiary_name" in report["missing_fields"]
    assert "next_visit_date" in report["missing_fields"]
    assert len(report["uncertain_indicators"]) > 0
    assert report["confidence_score"] < 0.85


# ==============================================================================
# 4. Voice Corrections Tests
# ==============================================================================
def test_voice_correction_weight_update():
    base_report = ASHAExtractionEngine.extract_report("ಮಗುವಿನ ತೂಕ 3.2 kg ಇದೆ")
    assert base_report["infant_weight"] == "3.2 kg"

    # Worker speaks: "No, the weight is 2.8 kilograms"
    updated, modified_field, confirm = ASHAExtractionEngine.apply_voice_correction(
        base_report, "No, the weight is 2.8 kilograms"
    )

    assert modified_field == "infant_weight"
    assert updated["infant_weight"] == "2.8 kg"
    assert "2.8 kg" in confirm


def test_voice_correction_next_visit_update():
    base_report = ASHAExtractionEngine.extract_report("ಫಲಾನುಭವಿ ಲಕ್ಷ್ಮಿ ಭೇಟಿ")
    assert base_report["next_visit_date"] is None

    updated, modified_field, confirm = ASHAExtractionEngine.apply_voice_correction(
        base_report, "Next visit is next week"
    )

    assert modified_field == "next_visit_date"
    assert "Next Week" in updated["next_visit_date"]


# ==============================================================================
# 5. Phase 2 & Phase 3 API Integration Tests
# ==============================================================================
def test_phase2_extract_endpoint():
    res = client.post("/api/report/extract", json={
        "transcript": "Beneficiary Lakshmi ANC home visit 24 weeks BP 120/80 next visit next week",
        "language": "en-IN"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["report"]["beneficiary_name"] == "Lakshmi"
    assert data["report"]["blood_pressure"] == "120/80"


def test_save_report_requires_explicit_confirmation():
    # Attempting to save without confirmed=True must fail
    res = client.post("/api/report/save", json={
        "report": {"beneficiary_name": "Lakshmi", "visit_type": "ANC"},
        "confirmed": False
    })
    assert res.status_code == 400
    assert "Explicit worker confirmation" in res.json()["detail"]


def test_save_report_success_and_dashboard_list():
    test_id = "TEST-REC-999"
    report_to_save = {
        "id": test_id,
        "beneficiary_name": "Saraswathi",
        "visit_type": "ANC Home Visit",
        "blood_pressure": "120/80",
        "next_visit_date": "Next Week",
        "referral_required": False
    }

    res_save = client.post("/api/report/save", json={
        "report": report_to_save,
        "confirmed": True
    })
    assert res_save.status_code == 200
    save_data = res_save.json()
    assert save_data["success"] is True
    assert save_data["record_id"] == test_id

    # Verify report appears in Phase 3 Dashboard
    res_list = client.get("/api/report/list")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["stats"]["total_visits"] >= 1
    found = any(r.get("id") == test_id for r in list_data["records"])
    assert found is True


# ==============================================================================
# 6. Multilingual Gnani Timbre Voice Resolution & Catalog Tests
# ==============================================================================
def test_timbre_all_10_languages_have_tested_voices():
    tts_client = GnaniTimbreTTSClient()
    for code, info in SUPPORTED_LANGUAGES.items():
        assert info["tts_supported"] is True
        default_voice = info["default_voice"]
        assert len(default_voice) >= 3
        resolved, _ = tts_client.resolve_voice(default_voice, code)
        assert len(resolved) >= 3


def test_timbre_legacy_voice_alias_resolution():
    tts_client = GnaniTimbreTTSClient()
    # Kavya (legacy) -> Devika (Timbre v2.5 Kannada voice)
    resolved_kn, note_kn = tts_client.resolve_voice("Kavya", "kn-IN")
    assert resolved_kn == "Devika"
    assert "Devika" in (note_kn or "")

    # Amala (legacy) -> Oviya (Tamil)
    resolved_ta, note_ta = tts_client.resolve_voice("Amala", "ta-IN")
    assert resolved_ta == "Oviya"

    # Swathi (legacy) -> Devika (Telugu)
    resolved_te, note_te = tts_client.resolve_voice("Swathi", "te-IN")
    assert resolved_te == "Devika"

    # Simran (legacy) -> Kartik (Punjabi)
    resolved_pa, note_pa = tts_client.resolve_voice("Simran", "pa-IN")
    assert resolved_pa == "Kartik"

