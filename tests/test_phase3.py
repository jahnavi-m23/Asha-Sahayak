"""
Comprehensive Test Suite for ASHA Sahayak Phase 3:
Database, Dashboard, and Follow-up Management.

Covers all required test scenarios:
- Saving confirmed visits
- Rejecting pending/unconfirmed visits
- Duplicate submissions prevention
- Missing required fields validation
- Beneficiary search and profile
- Visit history retrieval
- Follow-up dates handling (verifying no dates invented when null)
- Referral alerts and danger signs reflection
- Dashboard reports and synthetic statistics
- API error handling and status codes
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.database.crud import init_db, seed_database_if_empty

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_before_tests():
    """Resets database before test execution to ensure test isolation."""
    init_db()
    seed_database_if_empty(force=True)

def test_health_endpoint():
    """Validates health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "SQLite"

def test_save_confirmed_visit_exact_phase2_input():
    """
    Tests saving the exact structured visit record specified in Phase 2 contract:
    {
      "beneficiary_id": "BNF-2041",
      "visit_type": "Newborn home visit",
      "weight": "3.2 kg",
      "vaccinations_due": ["OPV-1"],
      "next_visit_date": null,
      "danger_signs": [],
      "referral_required": false,
      "confirmation_status": "confirmed"
    }
    """
    payload = {
        "beneficiary_id": "BNF-2041",
        "visit_type": "Newborn home visit",
        "weight": "3.2 kg",
        "vaccinations_due": ["OPV-1"],
        "next_visit_date": None,
        "danger_signs": [],
        "referral_required": False,
        "confirmation_status": "confirmed"
    }

    response = client.post("/api/visits/confirm", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "success"
    assert data["beneficiary_id"] == "BNF-2041"
    assert data["visit_type"] == "Newborn home visit"
    assert data["weight"] == "3.2 kg"
    assert "OPV-1" in data["vaccinations_due"]
    assert data["next_visit_date"] is None
    assert data["referral_required"] is False
    assert data["followup_created"] is False  # Must NOT invent date when null
    assert data["visit_id"].startswith("VIS-")

def test_reject_unconfirmed_or_pending_visit():
    """
    Ensures that only worker-confirmed visit records can be saved.
    Unconfirmed, pending, or draft records MUST be rejected with HTTP 400.
    """
    # Test pending status
    pending_payload = {
        "beneficiary_id": "BNF-2041",
        "visit_type": "Newborn home visit",
        "weight": "3.2 kg",
        "vaccinations_due": ["OPV-1"],
        "next_visit_date": None,
        "danger_signs": [],
        "referral_required": False,
        "confirmation_status": "pending"
    }
    res_pending = client.post("/api/visits/confirm", json=pending_payload)
    assert res_pending.status_code == 400
    assert "Only confirmed visit records can be saved" in res_pending.json()["detail"]

    # Test unconfirmed status
    unconfirmed_payload = pending_payload.copy()
    unconfirmed_payload["confirmation_status"] = "unconfirmed"
    res_unconfirmed = client.post("/api/visits/confirm", json=unconfirmed_payload)
    assert res_unconfirmed.status_code == 400
    assert "Only confirmed visit records can be saved" in res_unconfirmed.json()["detail"]

def test_duplicate_submission_prevention():
    """
    Tests that submitting the exact same confirmed visit twice is rejected
    with HTTP 409 Conflict and an informative error message.
    """
    payload = {
        "beneficiary_id": "BNF-2041",
        "visit_type": "Postnatal Day 14 Checkup",
        "weight": "3.5 kg",
        "vaccinations_due": ["OPV-1", "Pentavalent-1"],
        "next_visit_date": None,
        "danger_signs": [],
        "referral_required": False,
        "confirmation_status": "confirmed"
    }

    first_res = client.post("/api/visits/confirm", json=payload)
    assert first_res.status_code == 201

    # Second submission must be detected as duplicate
    second_res = client.post("/api/visits/confirm", json=payload)
    assert second_res.status_code == 409
    assert "Duplicate submission detected" in second_res.json()["detail"]

def test_missing_required_fields_validation():
    """Validates that omitting beneficiary_id or visit_type triggers validation error."""
    # Missing beneficiary_id
    payload_no_ben = {
        "visit_type": "Newborn home visit",
        "confirmation_status": "confirmed"
    }
    res1 = client.post("/api/visits/confirm", json=payload_no_ben)
    assert res1.status_code in (400, 422)

    # Missing visit_type
    payload_no_type = {
        "beneficiary_id": "BNF-2041",
        "confirmation_status": "confirmed"
    }
    res2 = client.post("/api/visits/confirm", json=payload_no_type)
    assert res2.status_code in (400, 422)

def test_followup_date_scheduled_when_provided():
    """
    Verifies that when a valid next_visit_date is provided by the worker,
    an upcoming follow-up record is automatically created in the database.
    """
    payload = {
        "beneficiary_id": "BNF-2041",
        "visit_type": "6-Week Routine Immunization",
        "weight": "4.1 kg",
        "vaccinations_due": ["OPV-1", "Pentavalent-1", "Rotavirus-1"],
        "next_visit_date": "2026-12-15",
        "danger_signs": [],
        "referral_required": False,
        "confirmation_status": "confirmed"
    }

    res = client.post("/api/visits/confirm", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["followup_created"] is True
    assert data["followup_id"] is not None

    # Verify follow-up appears in follow-up list
    fol_res = client.get("/api/followups?status=upcoming")
    assert fol_res.status_code == 200
    followups = fol_res.json()
    created_fol = next((f for f in followups if f["followup_id"] == data["followup_id"]), None)
    assert created_fol is not None
    assert created_fol["scheduled_date"] == "2026-12-15"
    assert created_fol["beneficiary_id"] == "BNF-2041"

def test_referral_alert_with_danger_signs():
    """
    Verifies that danger signs and referral flags received from Phase 2
    are stored and prominently marked for PHC referral without diagnosing.
    """
    payload = {
        "beneficiary_id": "BNF-2041",
        "visit_type": "Emergency Neonatal Assessment",
        "weight": "3.1 kg",
        "vaccinations_due": [],
        "next_visit_date": "2026-11-22",
        "danger_signs": ["High fever", "Poor sucking", "Chest indrawing"],
        "referral_required": True,
        "confirmation_status": "confirmed"
    }

    res = client.post("/api/visits/confirm", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["referral_required"] is True
    assert data["referral_status"] == "Pending PHC Referral"
    assert len(data["danger_signs"]) == 3

    # Check dashboard reports reflect the referral case
    rep_res = client.get("/api/reports")
    assert rep_res.status_code == 200
    reports = rep_res.json()
    assert reports["referral_cases"] >= 1
    # Check alert appears in recent alerts
    alert = next((a for a in reports["recent_referral_alerts"] if a["visit_id"] == data["visit_id"]), None)
    assert alert is not None
    assert "High fever" in alert["danger_signs"]

def test_beneficiary_search_and_records():
    """Tests searching beneficiaries by ID and name."""
    # Search by exact ID
    res_id = client.get("/api/beneficiaries?search=BNF-2041")
    assert res_id.status_code == 200
    results = res_id.json()
    assert len(results) >= 1
    assert any(b["beneficiary_id"] == "BNF-2041" for b in results)

    # Search by name substring
    res_name = client.get("/api/beneficiaries?search=Kavita")
    assert res_name.status_code == 200
    results_name = res_name.json()
    assert len(results_name) >= 1
    assert any("Kavita" in b["full_name"] for b in results_name)

def test_beneficiary_details_and_visit_history():
    """Tests viewing a specific beneficiary's profile, visits, and vaccination records."""
    res = client.get("/api/beneficiaries/BNF-1082")
    assert res.status_code == 200
    data = res.json()
    assert data["beneficiary"]["beneficiary_id"] == "BNF-1082"
    assert len(data["visits"]) >= 1
    assert "TT-2" in data["vaccinations_due"] or len(data["visits"][0]["vaccinations_due"]) > 0

    # Non-existent beneficiary returns 404
    res_404 = client.get("/api/beneficiaries/BNF-NONEXISTENT")
    assert res_404.status_code == 404

def test_followup_status_update_by_worker():
    """
    Tests updating the status of a scheduled follow-up (e.g. marking it completed
    and documenting field visit notes).
    """
    fol_res = client.get("/api/followups")
    assert fol_res.status_code == 200
    followups = fol_res.json()
    assert len(followups) > 0
    target_id = followups[0]["followup_id"]

    # Update to completed
    update_payload = {
        "status": "completed",
        "worker_notes": "Follow-up visit conducted. Both mother and child are doing well.",
        "worker_id": "ASHA-Rampur-1"
    }
    patch_res = client.patch(f"/api/followups/{target_id}/status", json=update_payload)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["status"] == "completed"
    assert "Follow-up visit conducted" in updated["worker_notes"]
    assert updated["completed_at"] is not None

def test_dashboard_reports_data():
    """
    Tests dashboard reports endpoint for accurate metric calculation
    and explicit labelling of synthetic data.
    """
    res = client.get("/api/reports")
    assert res.status_code == 200
    data = res.json()

    assert "SYNTHETIC DEMO DATA" in data["data_label"]
    assert data["total_beneficiaries"] >= 5
    assert data["total_completed_visits"] >= 4
    assert "upcoming_followups" in data
    assert "overdue_followups" in data
    assert "pending_followups" in data
    assert "referral_cases" in data
    assert isinstance(data["vaccinations_due_summary"], list)
    assert isinstance(data["recent_referral_alerts"], list)

def test_invalid_date_error_handling():
    """Tests that sending an invalid date format for next_visit_date is rejected with 400."""
    invalid_payload = {
        "beneficiary_id": "BNF-2041",
        "visit_type": "Newborn home visit",
        "weight": "3.2 kg",
        "vaccinations_due": ["OPV-1"],
        "next_visit_date": "next-wednesday",  # Invalid format
        "danger_signs": [],
        "referral_required": False,
        "confirmation_status": "confirmed"
    }
    res = client.post("/api/visits/confirm", json=invalid_payload)
    assert res.status_code == 400
    assert "next_visit_date must be in YYYY-MM-DD format" in res.json()["detail"]
