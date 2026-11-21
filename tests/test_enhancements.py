"""
Comprehensive Test Suite for ASHA Sahayak Enhancements:
- Authentication & Roles (Admin, ASHA Worker, Supervisor)
- Area & Pincode-Based Access Scoping
- Household Registration & Duplicate Prevention
- Family Members & Health Profiling
- Survey Management (Draft / Completed)
- Analytics & Infrastructure Aggregations
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.database.crud import init_db, seed_database_if_empty
from tests.client_util import DirectTestClient

client = DirectTestClient(app)

@pytest.fixture(autouse=True)
def reset_db_before_tests():
    init_db()
    seed_database_if_empty(force=True)

def test_login_successful_roles():
    """Tests successful login for Administrator, ASHA Worker, and Health Supervisor."""
    # 1. Admin login
    res_admin = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert data_admin["user"]["role"] == "admin"
    assert data_admin["access_token"] is not None

    # 2. ASHA Worker login
    res_asha = client.post("/api/auth/login", json={"username": "asha_rampur", "password": "asha123"})
    assert res_asha.status_code == 200
    data_asha = res_asha.json()
    assert data_asha["user"]["role"] == "asha_worker"
    assert data_asha["user"]["assigned_pincode"] == "571428"
    assert data_asha["user"]["assigned_village"] == "Rampur"

    # 3. Supervisor login
    res_sup = client.post("/api/auth/login", json={"username": "supervisor_maddur", "password": "sup123"})
    assert res_sup.status_code == 200
    data_sup = res_sup.json()
    assert data_sup["user"]["role"] == "health_supervisor"

def test_login_invalid_credentials():
    """Tests that incorrect password returns 401 Unauthorized."""
    res = client.post("/api/auth/login", json={"username": "asha_rampur", "password": "wrongpassword"})
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]

def test_forgot_password_assistance():
    """Tests forgot password endpoint verification."""
    res = client.post("/api/auth/forgot-password", json={"username": "asha_rampur"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "asha123" in data["message"]

def test_area_scoping_for_asha_worker():
    """
    Tests that an ASHA worker assigned to Rampur (571428) only views
    households in Rampur, and cannot see Kalyanpur (571434) households.
    """
    headers = {"Authorization": "Bearer token-asha_rampur-USR-ASHA-RAMPUR"}

    # Worker lists households
    res = client.get("/api/households", headers=headers)
    assert res.status_code == 200
    households = res.json()
    assert len(households) > 0
    # Every returned household must belong to Rampur / 571428
    for h in households:
        assert h["pincode"] == "571428"
        assert "Rampur" in h["village"]

    # Attempts to fetch a household from Kalyanpur (571434) must return 403 Forbidden
    res_forbidden = client.get("/api/households/HH-571434-001", headers=headers)
    assert res_forbidden.status_code == 403
    assert "Access Denied" in res_forbidden.json()["detail"]

def test_admin_global_access():
    """Tests that an Administrator can view households across all areas and PIN codes."""
    headers = {"Authorization": "Bearer token-admin-USR-ADMIN"}

    res = client.get("/api/households", headers=headers)
    assert res.status_code == 200
    households = res.json()
    # Should see households from both Rampur (571428) and Kalyanpur (571434)
    pincodes = {h["pincode"] for h in households}
    assert "571428" in pincodes
    assert "571434" in pincodes

def test_household_registration_with_family_health_profiling():
    """
    Tests registering a new household along with family members
    and configurable health indicators (pregnancy, child <5 immunization, elderly).
    """
    headers = {"Authorization": "Bearer token-asha_rampur-USR-ASHA-RAMPUR"}

    payload = {
        "area_id": "AREA-571428-1",
        "head_of_family": "Chikkanna Gowda",
        "address": "House # 112, North Lane, Rampur",
        "pincode": "571428",
        "village": "Rampur",
        "contact_number": "98765-99001",
        "house_type": "Pucca",
        "water_source": "Piped Water / Tap",
        "toilet_available": "Individual Household Latrine (IHHL)",
        "sanitation_facility": "Closed Drainage",
        "survey_status": "completed",
        "survey_date": "2026-11-21",
        "remarks": "Complete family survey conducted.",
        "family_members": [
            {
                "full_name": "Chikkanna Gowda",
                "age": 64,
                "gender": "Male",
                "dob": "1962-04-10",
                "relationship": "Self / Head",
                "mobile": "98765-99001",
                "occupation": "Farmer",
                "education": "Secondary",
                "marital_status": "Married",
                "is_elderly": True,
                "chronic_conditions": "Hypertension"
            },
            {
                "full_name": "Sowmya Gowda",
                "age": 24,
                "gender": "Female",
                "dob": "2002-09-15",
                "relationship": "Daughter-in-law",
                "mobile": "98765-99002",
                "occupation": "Homemaker",
                "education": "Higher Secondary",
                "marital_status": "Married",
                "is_pregnant": True,
                "pregnancy_trimester": "2nd Trimester"
            },
            {
                "full_name": "Baby Chetan",
                "age": 2,
                "gender": "Male",
                "dob": "2024-06-20",
                "relationship": "Grandchild",
                "is_child_under_5": True,
                "requires_immunization": True,
                "immunization_due": "MR-1, JE-1"
            }
        ]
    }

    res = client.post("/api/households", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["household"]["household_code"].startswith("HH-571428-")
    assert data["member_count"] == 3
    assert len(data["family_members"]) == 3

    # Check health profile persisted
    members = data["family_members"]
    pregnant = next((m for m in members if m["is_pregnant"] == 1), None)
    assert pregnant is not None
    assert pregnant["full_name"] == "Sowmya Gowda"
    assert pregnant["pregnancy_trimester"] == "2nd Trimester"

    child = next((m for m in members if m["is_child_under_5"] == 1), None)
    assert child is not None
    assert child["requires_immunization"] == 1

def test_duplicate_household_prevention():
    """Tests that registering an identical head of family and address is rejected with 409 Conflict."""
    headers = {"Authorization": "Bearer token-asha_rampur-USR-ASHA-RAMPUR"}

    payload = {
        "area_id": "AREA-571428-1",
        "head_of_family": "Ramesh Gowda",  # Existing in seed data
        "address": "House # 42, Near Maramma Temple, Rampur",  # Existing in seed data
        "pincode": "571428",
        "village": "Rampur"
    }

    res = client.post("/api/households", json=payload, headers=headers)
    assert res.status_code == 409
    assert "Duplicate Household Warning" in res.json()["detail"]

def test_survey_analytics_data():
    """Tests that the survey analytics endpoint returns accurate aggregated metrics."""
    headers = {"Authorization": "Bearer token-admin-USR-ADMIN"}

    res = client.get("/api/surveys/analytics", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_households_registered"] >= 5
    assert data["total_population_surveyed"] >= 10
    assert data["total_male_residents"] > 0
    assert data["total_female_residents"] > 0
    assert data["total_pregnant_women"] >= 1
    assert data["total_children_under_5"] >= 2
    assert data["total_elderly_residents"] >= 2
    assert "water_sources" in data["infrastructure"]
    assert "toilet_availability" in data["infrastructure"]
    assert "571428" in data["available_filters"]["pincodes"]
