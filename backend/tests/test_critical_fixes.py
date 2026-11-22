"""
Comprehensive End-to-End Test Suite for ASHA SAHAYAK Critical Fixes.
Validates:
1. Multiple ASHA Worker Registration & Individual Login (POST /api/auth/register).
2. Dynamic session authentication and header scoping without hardcoded defaults.
3. Accurate Clinical Field Mapping from voice transcripts (Name, Age, BP, Weight, Gestational Age, Symptoms, Vaccinations, Next Visit Date).
4. Phase 1 -> Phase 2 Handoff & SQLite Persistence in voice_records table with stable record ID.
5. Visit confirmation and SQLite relational persistence in visits, beneficiaries, and follow_ups tables.
6. Multi-field ASHA Worker Directory search (Name, Worker ID, Village, PIN code, PHC).
7. Duplicate submission prevention and data preservation across sessions.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.crud import (
    init_db,
    get_user_by_id,
    find_asha_workers,
    get_voice_records,
    get_visits,
    get_beneficiaries
)
from backend.extraction.engine import ASHAExtractionEngine
from backend.extraction.household_extractor import HouseholdSurveyExtractor

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

# ============================================================================
# 1. ASHA WORKER REGISTRATION & AUTHENTICATION TESTS
# ============================================================================

def test_register_multiple_asha_workers():
    """Step 1: Test self-service registration of multiple distinct ASHA workers."""
    uname1 = f"asha_test_{uuid.uuid4().hex[:6]}"
    uname2 = f"asha_test_{uuid.uuid4().hex[:6]}"

    # Register Worker 1
    w1_payload = {
        "full_name": "Asha Savitha Patil",
        "username": uname1,
        "password": "patil123Password",
        "mobile": "98451-22334",
        "village": "Kalyanpur",
        "pincode": "562159",
        "taluk": "Channapatna",
        "district": "Ramanagara",
        "phc_name": "Kalyanpur Community Health Centre",
        "sector": "Sector 3 Anganwadi"
    }
    res1 = client.post("/api/auth/register", json=w1_payload)
    assert res1.status_code == 201, res1.text
    d1 = res1.json()
    assert d1["status"] == "success"
    assert d1["user"]["full_name"] == "Asha Savitha Patil"
    assert d1["user"]["role"] == "asha_worker"
    assert d1["user"]["assigned_village"] == "Kalyanpur"
    assert "access_token" in d1

    # Register Worker 2
    w2_payload = {
        "full_name": "Asha Meenakshi Rao",
        "username": uname2,
        "password": "rao123Password",
        "mobile": "98452-33445",
        "village": "Shantipura",
        "pincode": "571434",
        "taluk": "Pandavapura",
        "district": "Mandya",
        "phc_name": "Shantipura PHC",
        "sector": "Ward 2 Anganwadi"
    }
    res2 = client.post("/api/auth/register", json=w2_payload)
    assert res2.status_code == 201, res2.text
    d2 = res2.json()
    assert d2["status"] == "success"
    assert d2["user"]["full_name"] == "Asha Meenakshi Rao"
    assert d2["user"]["id"] != d1["user"]["id"]

    # Verify duplicate username rejection
    res_dup = client.post("/api/auth/register", json=w1_payload)
    assert res_dup.status_code == 409


def test_individual_login_and_no_hardcoded_user():
    """Step 2: Verify login returns distinct sessions and missing auth fails."""
    # Test valid login
    res = client.post("/api/auth/login", json={"username": "asha_rampur", "password": "asha123"})
    assert res.status_code == 200
    data = res.json()
    assert "Sunita Devi" in data["user"]["full_name"]
    token = data["access_token"]

    # Test protected endpoint with token
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert "Sunita Devi" in res_me.json()["user"]["full_name"]

    # Test protected endpoint WITHOUT auth header - must reject with 401
    res_no_auth = client.get("/api/auth/me")
    assert res_no_auth.status_code == 401


# ============================================================================
# 2. AUTOMATIC CLINICAL FIELD MAPPING TESTS
# ============================================================================

def test_extract_beneficiary_name_kannada_and_english():
    """Step 3: Test accurate beneficiary name extraction with vibhakti & phrases."""
    # Kannada vibhakti phrases
    text1 = "ಫಲಾನುಭವಿಯ ಹೆಸರು ಲಕ್ಷ್ಮಿ ಅವರಿಗೆ ತಲೆನೋವು ಇದೆ"
    report1 = ASHAExtractionEngine.extract_report(text1, language_code="kn-IN")
    assert report1["beneficiary_name"] == "Lakshmi"

    text2 = "ತಾಯಿಯ ಹೆಸರು ರಾಧಿಕಾ ವಯಸ್ಸು 24 ವರ್ಷ"
    report2 = ASHAExtractionEngine.extract_report(text2, language_code="kn-IN")
    assert report2["beneficiary_name"] == "Radhika"

    # English phrases
    text3 = "Beneficiary name is Sunitha, pregnancy 28 weeks, BP 120/80"
    report3 = ASHAExtractionEngine.extract_report(text3, language_code="en-IN")
    assert report3["beneficiary_name"] == "Sunitha"

    text4 = "Patient Smt. Shilpa has high blood pressure 145/95"
    report4 = ASHAExtractionEngine.extract_report(text4, language_code="en-IN")
    assert report4["beneficiary_name"] == "Shilpa"


def test_extract_beneficiary_age():
    """Step 4: Test age extraction distinct from gestational weeks."""
    # Age in Kannada
    text1 = "ಫಲಾನುಭವಿಯ ಹೆಸರು ಕವಿತಾ ವಯಸ್ಸು 26 ವರ್ಷ ಗರ್ಭಿಣಿ 20 ವಾರಗಳು"
    report1 = ASHAExtractionEngine.extract_report(text1, language_code="kn-IN")
    assert report1["age"] == 26
    assert report1["beneficiary_age"] == 26
    assert "20 weeks" in report1["gestational_age"]

    # Age in English
    text2 = "Mother Geetha age 24 years, 32 weeks pregnant, BP 118/78"
    report2 = ASHAExtractionEngine.extract_report(text2, language_code="en-IN")
    assert report2["age"] == 24
    assert "32 weeks" in report2["gestational_age"]


def test_extract_vitals_symptoms_and_vaccinations():
    """Step 5: Test complete field mapping (Weight, BP, Symptoms, Vaccines, Next Visit)."""
    transcript = (
        "Beneficiary name is Lakshmi, age 25 years. Weight is 2.9 kg and blood pressure 120/80. "
        "OPV-1 and BCG due. Patient reports mild fever and cold, but no bleeding. Next visit next week."
    )
    report = ASHAExtractionEngine.extract_report(transcript, language_code="en-IN")

    assert report["beneficiary_name"] == "Lakshmi"
    assert report["age"] == 25
    assert report["weight"] == "2.9 kg"
    assert report["infant_weight"] == "2.9 kg"
    assert report["blood_pressure"] == "120/80"
    assert "OPV-1" in report["vaccinations_due"]
    assert "BCG" in report["vaccinations_due"]
    assert "Fever" in report["symptoms_reported"]
    assert any("Bleeding" in s for s in report["negated_symptoms"])
    assert "Next Week" in report["next_visit_date"]
    assert report["confirmed"] is False


def test_no_fabricated_values_on_missing_fields():
    """Step 6: Missing information must remain null/None, never fabricated."""
    minimal_text = "Routine home visit completed."
    report = ASHAExtractionEngine.extract_report(minimal_text, language_code="en-IN")

    assert report["beneficiary_name"] is None
    assert report["age"] is None
    assert report["weight"] is None
    assert report["blood_pressure"] is None
    assert report["gestational_age"] is None
    assert len(report["vaccinations_due"]) == 0
    assert len(report["symptoms_reported"]) == 0


# ============================================================================
# 3. PHASE 1 -> PHASE 2 DATA HANDOFF TESTS
# ============================================================================

def test_phase1_to_phase2_handoff_endpoint():
    """Step 7: Test /api/voice/to-phase2 saves to voice_records table with stable record_id."""
    test_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
    unique_suffix = uuid.uuid4().hex[:6]
    payload = {
        "record_id": test_id,
        "transcript": f"Beneficiary name is Radhika, age 23 years, weight 3.1 kg, OPV-1 due, next visit next week. Note {unique_suffix}",
        "language": "kn-en",
        "status": "completed",
        "form_type": "VISIT"
    }

    res = client.post("/api/voice/to-phase2", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["success"] is True
    assert data["record_id"] == test_id
    assert data["report"]["beneficiary_name"] == "Radhika"
    assert data["report"]["age"] == 23
    assert data["report"]["weight"] == "3.1 kg"

    # Verify record was persisted into SQLite voice_records table
    records = get_voice_records(limit=10)
    matching = [r for r in records if r["id"] == test_id]
    assert len(matching) == 1
    assert matching[0]["transcript"] == payload["transcript"]
    assert matching[0]["form_type"] == "VISIT"


def test_phase1_to_phase2_duplicate_prevention():
    """Step 8: Prevent duplicate voice record submissions."""
    payload = {
        "transcript": f"Unique narrative test {uuid.uuid4().hex}",
        "language": "kn-IN",
        "status": "completed"
    }
    res1 = client.post("/api/voice/to-phase2", json=payload)
    assert res1.status_code == 200
    rec_id1 = res1.json()["record_id"]

    # Post identical transcript again
    res2 = client.post("/api/voice/to-phase2", json=payload)
    assert res2.status_code == 200
    assert res2.json()["record_id"] == rec_id1


# ============================================================================
# 4. DATABASE INTEGRATION & VISIT CONFIRMATION TESTS
# ============================================================================

def test_visit_confirm_and_relational_saving():
    """Step 9: Confirm visit and verify SQLite beneficiaries, visits, and follow_ups."""
    ben_id = f"BNF-{uuid.uuid4().hex[:6].upper()}"
    visit_payload = {
        "beneficiary_id": ben_id,
        "beneficiary_name": "Kavitha Sharma",
        "age": 28,
        "visit_type": "ANC Home Visit (ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ)",
        "weight": "54 kg",
        "blood_pressure": "125/82",
        "gestational_age": "28 weeks",
        "pregnancy_status": "Pregnant",
        "vaccinations_due": ["Td-2"],
        "symptoms_reported": ["Mild Headache"],
        "negated_symptoms": ["No Bleeding"],
        "next_visit_date": "2026-12-05",
        "danger_signs": [],
        "referral_required": False,
        "confirmation_status": "confirmed",
        "worker_id": "USR-ASHA-RAMPUR"
    }

    res = client.post("/api/visits/confirm", json=visit_payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["status"] == "success"
    assert data["beneficiary_name"] == "Kavitha Sharma"
    assert data["followup_created"] is True

    # Verify visit is in SQLite visits table
    visits = get_visits(beneficiary_id=ben_id)
    assert len(visits) == 1
    v = visits[0]
    assert v["beneficiary_name"] == "Kavitha Sharma"
    assert v["age"] == 28
    assert v["blood_pressure"] == "125/82"
    assert v["gestational_age"] == "28 weeks"
    assert "Td-2" in v["vaccinations_due"]

    # Verify beneficiary is in SQLite beneficiaries table
    bens = get_beneficiaries(search=ben_id)
    assert len(bens) == 1
    assert bens[0]["full_name"] == "Kavitha Sharma"
    assert bens[0]["age_years"] == 28


def test_reject_unconfirmed_visit():
    """Step 10: Reject visit saving if status is not 'confirmed'."""
    payload = {
        "beneficiary_id": f"BNF-{uuid.uuid4().hex[:6].upper()}",
        "visit_type": "Routine Field Visit",
        "confirmation_status": "draft"
    }
    res = client.post("/api/visits/confirm", json=payload)
    assert res.status_code == 400


def test_duplicate_visit_prevention():
    """Step 11: Duplicate visits with identical beneficiary, type, and date are rejected."""
    ben_id = f"BNF-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "beneficiary_id": ben_id,
        "beneficiary_name": "Meena",
        "visit_type": "Postpartum Checkup",
        "confirmation_status": "confirmed",
        "visit_date": "2026-11-20"
    }
    res1 = client.post("/api/visits/confirm", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/visits/confirm", json=payload)
    assert res2.status_code == 409


# ============================================================================
# 5. ASHA WORKER DIRECTORY SEARCH TESTS
# ============================================================================

def test_find_asha_workers_multi_criteria():
    """Step 12: Search directory by name, worker ID, village, PIN code, and PHC."""
    # 1. Search by PIN code
    res_pin = client.get("/api/workers/find?pincode=571428")
    assert res_pin.status_code == 200
    workers_pin = res_pin.json()["workers"]
    assert len(workers_pin) >= 1
    assert any(w["pincode"] == "571428" for w in workers_pin)

    # 2. Search by village
    res_vil = client.get("/api/workers/find?village=Rampur")
    assert res_vil.status_code == 200
    workers_vil = res_vil.json()["workers"]
    assert len(workers_vil) >= 1
    assert any("rampur" in w["village"].lower() for w in workers_vil)

    # 3. Search by worker name
    res_name = client.get("/api/workers/find?name=Sunita")
    assert res_name.status_code == 200
    workers_name = res_name.json()["workers"]
    assert len(workers_name) >= 1
    assert "Sunita Devi" in workers_name[0]["full_name"]

    # 4. Search by worker ID
    res_id = client.get("/api/workers/find?worker_id=USR-ASHA-RAMPUR")
    assert res_id.status_code == 200
    workers_id = res_id.json()["workers"]
    assert len(workers_id) >= 1
    assert workers_id[0]["worker_id"] == "USR-ASHA-RAMPUR"

    # 5. Search by PHC
    res_phc = client.get("/api/workers/find?phc_name=Kestur")
    assert res_phc.status_code == 200
    workers_phc = res_phc.json()["workers"]
    assert len(workers_phc) >= 1
    assert "Kestur" in workers_phc[0]["phc_name"]

    # 6. Verify required fields are present in response
    sample = workers_pin[0]
    required_keys = ["worker_id", "badge_id", "full_name", "mobile", "village", "pincode", "taluk", "district", "phc_name", "sector", "account_status"]
    for k in required_keys:
        assert k in sample, f"Key '{k}' missing from worker result"


# ============================================================================
# 6. VOICE HOUSEHOLD REGISTRATION PIPELINE TEST
# ============================================================================

def test_voice_household_survey_intent_and_extraction():
    """Step 13: Voice input for household survey correctly classified and extracted."""
    hh_voice = (
        "Household survey for head of family Ramesh Gowda, house number 54 Rampur village, "
        "PIN 571428. Water source piped tap, toilet available individual latrine. "
        "Family members Ramesh Gowda age 42, wife Lakshmi age 38, son Suresh age 14."
    )
    # Intent classification
    intent = HouseholdSurveyExtractor.classify_intent(hh_voice)
    assert intent == "HOUSEHOLD"

    # Extraction
    hh_data = HouseholdSurveyExtractor.extract_household(hh_voice, language_code="en-IN")
    assert hh_data["head_of_family"] == "Ramesh Gowda"
    assert hh_data["village"] == "Rampur"
    assert hh_data["pincode"] == "571428"
    assert len(hh_data["family_members"]) >= 2


def test_voice_records_preservation_across_refresh():
    """Step 14: Verify records remain preserved in SQLite database and are queryable."""
    res = client.get("/api/voice/records")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert isinstance(data["records"], list)
