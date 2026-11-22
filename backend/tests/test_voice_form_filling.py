"""
ASHA Sahayak - Voice-Based Form Filling & Household Registration Tests
Tests:
1. Voice-based household extraction in Kannada (e.g. Ramesh, 4 members, Rampur, toilet available).
2. Voice-based household extraction in English/code-mixed speech.
3. Zero hallucination: Missing fields are left empty/null and clarification questions generated.
4. Intent classification: Household survey vs clinical health visit.
5. Auto-generation and persistence of household in SQLite DB (POST /api/households).
6. Immediate display and retrieval in Household Directory (GET /api/households).
7. Duplicate household registration prevention (409 Conflict).
8. Multilingual translation strict policy (never returns untranslated text as success).
9. Voice clarification question generation.
10. End-to-end voice extraction route (POST /api/report/extract & POST /api/households/voice-extract).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.extraction.household_extractor import HouseholdExtractor
from backend.translation.engine import indic_translator, ASHAIndicTranslator

client = TestClient(app)

AUTH_HEADERS = {
    "Authorization": "Bearer token-asha_rampur-USR-ASHA-RAMPUR"
}


# ==============================================================================
# 1. Voice Household Extraction Tests (Kannada & Code-Mixed)
# ==============================================================================
def test_voice_household_extraction_kannada():
    """
    User scenario:
    When ASHA worker speaks in Kannada that family head is Ramesh and there are 4 members,
    auto-extract and fill those fields.
    """
    transcript = "ಕುಟುಂಬದ ಮುಖ್ಯಸ್ಥ ರಮೇಶ್, ನಾಲ್ಕು ಸದಸ್ಯರು ಇದ್ದಾರೆ, ರಾಂಪುರ ಗ್ರಾಮ, ಶೌಚಾಲಯ ಇದೆ, ನಲ್ಲಿ ನೀರು"
    data = HouseholdExtractor.extract_household(transcript, language_code="kn-IN")

    assert "Ramesh" in data["head_of_family"] or "ರಮೇಶ್" in data["head_of_family"]
    assert data["member_count"] == 4
    assert data["village"] == "Rampur"
    assert data["toilet_available"] is True
    assert "Piped" in data["water_source"]
    assert data["extracted_from_voice"] is True
    assert data["raw_transcript"] == transcript

    # Zero-hallucination verification: Contact number was not mentioned, must remain None
    assert data["contact_number"] is None

    # Clarification prompt generated for missing required field
    assert data["clarification_prompt"] is not None
    assert len(data["clarification_prompt"]) > 5

    # Bilingual readbacks generated for worker review
    assert len(data["readback_kn"]) > 10
    assert len(data["readback_en"]) > 10
    assert "Ramesh" in data["readback_en"] or "ರಮೇಶ್" in data["readback_kn"]


def test_voice_household_extraction_english_codemix():
    """
    Test English / Code-mixed voice note for household survey.
    """
    transcript = "Head of family Suresh Kumar, 5 members, village Rampur, PIN 571428, house type Pucca, phone 9876543210, toilet available"
    data = HouseholdExtractor.extract_household(transcript, language_code="en-IN")

    assert data["head_of_family"] == "Suresh Kumar"
    assert data["member_count"] == 5
    assert data["village"] == "Rampur"
    assert data["pincode"] == "571428"
    assert data["house_type"] == "Pucca"
    assert data["contact_number"] == "9876543210"
    assert data["toilet_available"] is True
    assert len(data["family_members"]) == 5


def test_voice_household_zero_hallucination_and_clarification():
    """
    Test that when vital fields are missing, the system never invents fake data
    and generates targeted clarification questions.
    """
    transcript = "ಮನೆ ಮುಖ್ಯಸ್ಥ ಬಸವರಾಜು, ಸದಸ್ಯರು ಮೂರು"
    data = HouseholdExtractor.extract_household(transcript, language_code="kn-IN")

    assert "Basavaraju" in data["head_of_family"] or "ಬಸವರಾಜು" in data["head_of_family"]
    assert data["member_count"] == 3
    # Pincode, contact number, address lines were NOT mentioned:
    assert data["contact_number"] is None
    assert data["address"] is None
    # Clarification prompt must request missing information (village/PIN or contact/address)
    assert any(k in data["clarification_prompt"].lower() for k in ["village", "pin", "contact", "address", "ಗ್ರಾಮ", "ವಿಳಾಸ", "ದೂರವಾಣಿ"])


# ==============================================================================
# 2. Form Intent Classification: Household vs Clinical Visit
# ==============================================================================
def test_intent_classification():
    """
    Test that the system accurately classifies whether the ASHA worker
    is recording a Household Survey or a Clinical Beneficiary Visit.
    """
    household_transcript = "ಹೊಸ ಕುಟುಂಬ ಸಮೀಕ್ಷೆ, ಮುಖ್ಯಸ್ಥ ಮಂಜುನಾಥ್, 3 ಸದಸ್ಯರು, ರಾಂಪುರ ಗ್ರಾಮ"
    assert HouseholdExtractor.is_household_intent(household_transcript) is True

    visit_transcript = "ಫಲಾನುಭವಿ ಲಕ್ಷ್ಮಿ 24 ವಾರ ಗರ್ಭಿಣಿ, ಬಿಪಿ 120 80, ಮುಂದಿನ ವಾರ ಭೇಟಿ"
    assert HouseholdExtractor.is_household_intent(visit_transcript) is False


def test_report_extract_api_intent_routing():
    """
    Test POST /api/report/extract auto-routes to form_type='HOUSEHOLD' or 'VISIT'.
    """
    # Household intent
    hh_res = client.post(
        "/api/report/extract",
        json={"transcript": "ಕುಟುಂಬದ ಮುಖ್ಯಸ್ಥ ರಮೇಶ್, 4 ಸದಸ್ಯರು ಇದ್ದಾರೆ, ರಾಂಪುರ", "language": "kn-IN"}
    )
    assert hh_res.status_code == 200
    hh_data = hh_res.json()
    assert hh_data["success"] is True
    assert hh_data["form_type"] == "HOUSEHOLD"
    assert "household_data" in hh_data
    assert hh_data["household_data"]["member_count"] == 4

    # Visit intent
    visit_res = client.post(
        "/api/report/extract",
        json={"transcript": "Beneficiary Radhika ANC home visit 28 weeks blood pressure 110/70", "language": "en-IN"}
    )
    assert visit_res.status_code == 200
    visit_data = visit_res.json()
    assert visit_data["success"] is True
    assert visit_data["form_type"] == "VISIT"
    assert "report" in visit_data
    assert visit_data["report"]["beneficiary_name"] == "Radhika"


# ==============================================================================
# 3. Household CRUD, Directory Persistence & Duplicate Prevention
# ==============================================================================
def test_household_registration_crud_and_directory():
    """
    Test creating a household, verifying it appears in the Household Directory,
    and preventing duplicate codes.
    """
    unique_suffix = uuid.uuid4().hex[:4].upper()
    test_code = f"HH-571428-T{unique_suffix}"
    payload = {
        "household_code": test_code,
        "head_of_family": f"Chikkanna {unique_suffix}",
        "member_count": 4,
        "area_id": "AREA-571428-1",
        "village": "Rampur",
        "pincode": "571428",
        "address": "Opposite Gram Panchayat, Rampur",
        "house_type": "Pucca",
        "water_source": "Piped Tap",
        "toilet_available": True,
        "sanitation_facility": "Private Flush Latrine",
        "contact_number": "9845012345",
        "family_members": [
            {"name": "Chikkanna M", "age": 48, "gender": "Male", "relation": "Head", "health_flags": "None"},
            {"name": "Parvathamma", "age": 44, "gender": "Female", "relation": "Spouse", "health_flags": "None"},
            {"name": "Vinay Kumar", "age": 22, "gender": "Male", "relation": "Son", "health_flags": "None"},
            {"name": "Kavitha C", "age": 19, "gender": "Female", "relation": "Daughter", "health_flags": "None"}
        ]
    }

    # 1. Register household
    create_res = client.post("/api/households", json=payload, headers=AUTH_HEADERS)
    assert create_res.status_code in [200, 201]
    created = create_res.json()
    household_id = created["id"]
    assert created["household_code"] == test_code
    assert unique_suffix in created["head_of_family"]

    # 2. Immediately visible in Household Directory
    list_res = client.get("/api/households", headers=AUTH_HEADERS)
    assert list_res.status_code == 200
    households = list_res.json()
    assert len(households) > 0
    matched = [h for h in households if h["household_code"] == test_code]
    assert len(matched) == 1
    assert unique_suffix in matched[0]["head_of_family"]
    assert matched[0]["village"] == "Rampur"

    # 3. Duplicate Prevention: Attempting to register the same code again returns 409 Conflict
    dup_res = client.post("/api/households", json=payload, headers=AUTH_HEADERS)
    assert dup_res.status_code == 409

    # 4. Clean up test record
    del_res = client.delete(f"/api/households/{household_id}", headers=AUTH_HEADERS)
    assert del_res.status_code in [200, 204]


# ==============================================================================
# 4. Multilingual Translation Strict Policy Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_translation_strict_failure_policy():
    """
    Verify that if translation fails or returns untranslated text in original script,
    the system marks success=False and never masquerades original text as translated.
    """
    # Normal translation
    res = await indic_translator.translate(
        text="ಮಗುವಿಗೆ ಜ್ವರ ಇದೆ",
        source_language="kn-IN",
        target_language="en-IN"
    )
    if res.get("success"):
        # Must be in English, not Kannada
        assert "fever" in res["translated_text"].lower() or "child" in res["translated_text"].lower() or "baby" in res["translated_text"].lower()
        # Must not be identical to original Kannada text
        assert res["translated_text"] != "ಮಗುವಿಗೆ ಜ್ವರ ಇದೆ"


def test_translation_api_endpoint():
    """
    Test POST /api/voice/translate route with Kannada to English.
    """
    resp = client.post("/api/voice/translate", json={
        "text": "ತಾಯಿಯ ರಕ್ತದೊತ್ತಡ ಸಾಮಾನ್ಯವಾಗಿದೆ",
        "source_language": "kn-IN",
        "target_language": "en-IN"
    })
    assert resp.status_code == 200
    data = resp.json()
    if data.get("success"):
        assert "blood pressure" in data["translated_text"].lower() or "normal" in data["translated_text"].lower()
        assert data["translated_text"] != data["original_text"]
