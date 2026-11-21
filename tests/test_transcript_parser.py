# tests/test_transcript_parser.py
"""
Tests for multilingual transcript parsing, entity preservation, and normalization.
Covers:
- English transcripts
- Kannada transcripts
- Kannada-English mixed transcripts (kn-en)
- Medical terms and vaccination names
- Kannada numerals (೦-೯) and number words
- Incomplete and ambiguous statements
"""
import pytest
from backend.ai.transcript_parser import TranscriptParser


def test_transcript_normalization():
    # Audio filler words and spaces
    raw = "uh, the baby  weight [cough] is 3.2 kg  "
    clean = TranscriptParser.normalize_transcript(raw)
    assert clean == "the baby weight is 3.2 kg"


def test_kannada_digit_normalization():
    # Kannada digits ೩.೨ -> 3.2
    raw = "ಮಗುವಿನ ತೂಕ ೩.೨ ಕೆಜಿ"
    clean = TranscriptParser.normalize_transcript(raw)
    assert "3.2" in clean


def test_weight_extraction_english():
    assert TranscriptParser.extract_weight("The baby weight is 3.2 kg") == "3.2 kg"
    assert TranscriptParser.extract_weight("weight 2.8 kilograms") == "2.8 kg"
    assert TranscriptParser.extract_weight("wt: 3.5") == "3.5 kg"


def test_weight_extraction_kannada():
    assert TranscriptParser.extract_weight("ಮಗುವಿನ ತೂಕ ೩.೨ ಕೆಜಿ") == "3.2 kg"
    assert TranscriptParser.extract_weight("ತೂಕ 2.8 ಕಿಲೋಗ್ರಾಂ") == "2.8 kg"


def test_weight_extraction_spoken_kannada():
    # Spoken numbers: "ಮೂರು point ಎರಡು ಕೆಜಿ" -> 3.2 kg
    text = "ಮಗುವಿನ ತೂಕ ಮೂರು point ಎರಡು ಕೆಜಿ ಆಗಿದೆ"
    assert TranscriptParser.extract_weight(text) == "3.2 kg"


def test_weight_extraction_grams_to_kg():
    # 3200 grams -> 3.20 kg
    assert TranscriptParser.extract_weight("baby is 3200 grams") == "3.20 kg"


def test_weight_incorrect_out_of_bounds():
    # A human newborn or mother weight cannot be 500 kg or 0.1 kg
    assert TranscriptParser.extract_weight("weight is 800 kg") is None
    assert TranscriptParser.extract_weight("weight is 0.1 kg") is None


def test_vaccination_extraction_standard():
    assert TranscriptParser.extract_vaccinations("OPV-1 is due today") == ["OPV-1"]
    assert "BCG" in TranscriptParser.extract_vaccinations("give BCG and OPV 0")
    assert "Pentavalent-1" in TranscriptParser.extract_vaccinations("penta-1 vaccine due")
    assert "Rotavirus-1" in TranscriptParser.extract_vaccinations("rotavirus 1 and fIPV 1")


def test_vaccination_extraction_kannada():
    assert "BCG" in TranscriptParser.extract_vaccinations("ಮಗುವಿಗೆ ಬಿಸಿಜಿ ಲಸಿಕೆ ಹಾಕಬೇಕು")
    assert "OPV-1" in TranscriptParser.extract_vaccinations("ಒಪಿವಿ-1 ಮತ್ತು ಪೆಂಟಾವಲೆಂಟ್ ಬಾಕಿ ಇದೆ")


def test_vaccination_extraction_code_mixed():
    text = "Baby ge OPV-1 and BCG vaccine due ide"
    vaccines = TranscriptParser.extract_vaccinations(text)
    assert "OPV-1" in vaccines
    assert "BCG" in vaccines


def test_beneficiary_id_extraction():
    assert TranscriptParser.extract_beneficiary_id("Beneficiary BNF-2041 visited") == "BNF-2041"
    assert TranscriptParser.extract_beneficiary_id("ID BNF2041") == "BNF-2041"
    assert TranscriptParser.extract_beneficiary_id("ಫಲಾನುಭವಿ ಸಂಖ್ಯೆ BNF-9988") == "BNF-9988"
    assert TranscriptParser.extract_beneficiary_id("No id mentioned here") is None


def test_next_visit_date_extraction():
    assert TranscriptParser.extract_next_visit_date("next visit on 2026-11-28") == "2026-11-28"
    assert TranscriptParser.extract_next_visit_date("date is 15/12/2026") == "2026-12-15"
    assert TranscriptParser.extract_next_visit_date("no date mentioned") is None


def test_infer_visit_type():
    assert TranscriptParser.infer_visit_type("baby visit home checkup") == "Newborn home visit"
    assert TranscriptParser.infer_visit_type("ANC checkup done for mother") == "Antenatal Care (ANC)"
    assert TranscriptParser.infer_visit_type("ಗರ್ಭಿಣಿ ತಪಾಸಣೆ") == "Antenatal Care (ANC)"
    assert TranscriptParser.infer_visit_type("ಹೆರಿಗೆಯ ನಂತರದ ಭೇಟಿ") == "Postnatal Care (PNC)"


def test_detect_ambiguity_and_incompletion():
    is_ambiguous, reasons = TranscriptParser.detect_ambiguity_or_incompletion("The baby weight is...")
    assert is_ambiguous
    assert "unclear_trailing_speech" in reasons or "weight_unclear" in reasons

    is_ambiguous, reasons = TranscriptParser.detect_ambiguity_or_incompletion("vaccine is due today")
    assert is_ambiguous
    assert "vaccine_unspecified" in reasons
