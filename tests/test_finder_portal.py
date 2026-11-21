"""
Integration and Unit Test Suite for:
ASHA SAHAYAK – LOCATION-BASED ASHA WORKER FINDER AND LOGIN PORTAL

Covers 10 Required Test Scenarios:
1. Search by PIN code
2. Search by village name
3. Search by district
4. Search an area with multiple ASHA workers (Rampur: Sunita Devi & Anasuya Bai)
5. Search an area without registered workers (Shantipura: helpful message)
6. Login with valid worker credentials (via Badge ID & Username)
7. Attempt login with invalid credentials (rejected)
8. Verify worker authorization scoping (worker only sees designated households)
9. Admin reassigns village/area to another worker
10. Public search reflects updated assignment immediately
"""

import os
import sys
from pathlib import Path

# Set up project root in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.crud import (
    init_db,
    seed_database_if_empty,
    find_asha_workers,
    authenticate_user,
    get_worker_dashboard_summary,
    admin_list_workers,
    admin_register_worker,
    admin_update_worker,
    admin_reset_worker_password,
    supervisor_get_overview,
    get_households,
    get_audit_logs,
)
from backend.routes.workers import public_find_asha_workers, WorkerUpdateRequest
from backend.routes.auth import LoginRequest, login

def run_all_tests():
    print("=" * 70)
    print("RUNNING ASHA SAHAYAK FINDER & LOGIN PORTAL VERIFICATION SUITE")
    print("=" * 70)

    # Reset and seed database
    init_db()
    seed_database_if_empty(force=True)

    passed_count = 0
    total_count = 10

    # ------------------------------------------------------------------------
    # SCENARIO 1: Search by PIN code
    # ------------------------------------------------------------------------
    print("\n[Scenario 1] Testing search by PIN code '571428'...")
    res1 = find_asha_workers(pincode="571428")
    assert len(res1) >= 2, f"Expected at least 2 workers for 571428, found {len(res1)}"
    for w in res1:
        assert w["pincode"] == "571428"
        assert "password_hash" not in w
        assert w["is_verified"] is True
    print(f"  PASS: Found {len(res1)} verified workers in PIN 571428 (Sanitized output verified).")
    passed_count += 1

    # ------------------------------------------------------------------------
    # SCENARIO 2: Search by village name
    # ------------------------------------------------------------------------
    print("\n[Scenario 2] Testing search by village name 'Kalyanpur'...")
    res2 = find_asha_workers(village="Kalyanpur")
    assert len(res2) == 1, f"Expected 1 worker for Kalyanpur, found {len(res2)}"
    assert res2[0]["village"] == "Kalyanpur"
    assert res2[0]["badge_id"] == "ASHA-KA-MDY-003"
    print(f"  PASS: Correctly found worker '{res2[0]['full_name']}' ({res2[0]['badge_id']}) in Kalyanpur.")
    passed_count += 1

    # ------------------------------------------------------------------------
    # SCENARIO 3: Search by district
    # ------------------------------------------------------------------------
    print("\n[Scenario 3] Testing search by district 'Mandya'...")
    res3 = find_asha_workers(district="Mandya")
    assert len(res3) >= 3, f"Expected at least 3 workers in Mandya, found {len(res3)}"
    villages = {w["village"] for w in res3}
    assert "Rampur" in villages and "Kalyanpur" in villages
    print(f"  PASS: Found {len(res3)} workers across Mandya district villages: {villages}.")
    passed_count += 1

    # ------------------------------------------------------------------------
    # SCENARIO 4: Search an area with multiple ASHA workers
    # ------------------------------------------------------------------------
    print("\n[Scenario 4] Testing area with multiple ASHA workers (Rampur)...")
    res4 = find_asha_workers(village="Rampur")
    assert len(res4) == 2, f"Expected 2 workers in Rampur, found {len(res4)}"
    badge_ids = {w["badge_id"] for w in res4}
    assert "ASHA-KA-MDY-001" in badge_ids, "Missing Sunita Devi (ASHA-KA-MDY-001)"
    assert "ASHA-KA-MDY-002" in badge_ids, "Missing Anasuya Bai (ASHA-KA-MDY-002)"
    # Check that each covers a designated sector
    wards = {w["area_name"] for w in res4}
    assert len(wards) == 2, f"Workers must have distinct sector areas: {wards}"
    print(f"  PASS: Multi-worker resolution verified for Rampur: {badge_ids} in wards {wards}.")
    passed_count += 1

    # ------------------------------------------------------------------------
    # SCENARIO 5: Search an area without registered workers
    # ------------------------------------------------------------------------
    print("\n[Scenario 5] Testing search for unassigned area (Shantipura / 562160)...")
    res5 = public_find_asha_workers(village="Shantipura")
    assert res5["total_found"] == 0
    assert len(res5["workers"]) == 0
    assert "No verified ASHA workers found" in res5["message"]
    assert "Primary Health Centre" in res5["message"]
    print(f"  PASS: Friendly guidance message returned: '{res5['message']}'")
    passed_count += 1

    # ------------------------------------------------------------------------
    # SCENARIO 6: Login with valid worker credentials
    # ------------------------------------------------------------------------
    print("\n[Scenario 6] Testing login with valid worker credentials...")
    # Test 6A: Login using official badge ID
    auth_badge = authenticate_user("ASHA-KA-MDY-001", "asha123")
    assert auth_badge is not None, "Failed login via Badge ID ASHA-KA-MDY-001"
    assert auth_badge["username"] == "asha_rampur"
    assert auth_badge["role"] == "asha_worker"
    assert "password_hash" not in auth_badge

    # Test 6B: Login using username via API route
    login_resp = login(LoginRequest(username="asha_rampur", password="asha123"))
    assert login_resp["status"] == "success"
    assert "token-" in login_resp["access_token"]
    assert login_resp["user"]["id"] == "USR-ASHA-RAMPUR"

    # Test 6C: Check worker dashboard summary returns 8 navigation paths
    dash = get_worker_dashboard_summary("USR-ASHA-RAMPUR")
    assert "metrics" in dash
    assert dash["metrics"]["total_households"] > 0
    assert len(dash["quick_navigation"]) == 8, f"Expected 8 navigation paths, got {len(dash['quick_navigation'])}"
    print(f"  PASS: Successfully authenticated via Badge ID and Username. Worker dashboard verified with 8 quick paths.")
    passed_count += 1

    # ------------------------------------------------------------------------
    # SCENARIO 7: Attempt login with invalid credentials
    # ------------------------------------------------------------------------
    print("\n[Scenario 7] Testing login with invalid credentials...")
    # 7A: Wrong password
    bad_pwd = authenticate_user("asha_rampur", "wrongpass999")
    assert bad_pwd is None, "Expected authentication failure on wrong password"

    # 7B: Non-existent user/badge
    bad_user = authenticate_user("NON_EXISTENT_WORKER", "asha123")
    assert bad_user is None, "Expected authentication failure on unknown user"
    print("  PASS: Invalid credentials correctly rejected (HTTP 401 behavior verified).")
    passed_count += 1

    # ------------------------------------------------------------------------
    # SCENARIO 8: Verify worker authorization scoping
    # ------------------------------------------------------------------------
    print("\n[Scenario 8] Testing authorization scoping for ASHA Rampur...")
    worker_user = {
        "id": "USR-ASHA-RAMPUR",
        "username": "asha_rampur",
        "role": "asha_worker",
        "assigned_area_id": "AREA-571428-1"
    }
    scoped_hh = get_households(user=worker_user)
    for h in scoped_hh:
        assert h["area_id"] == "AREA-571428-1" or h["created_by_worker_id"] == "USR-ASHA-RAMPUR"
        assert h["village"] != "Kalyanpur", "Worker illegally accessed Kalyanpur households!"
    print(f"  PASS: Worker access strictly constrained to designated area (retrieved {len(scoped_hh)} households, 0 cross-area leaks).")
    passed_count += 1

    # ------------------------------------------------------------------------
    # SCENARIO 9: Admin reassigns village to another worker
    # ------------------------------------------------------------------------
    print("\n[Scenario 9] Testing administrative reassignment of Shantipura to Anasuya Bai...")
    admin_update_worker(
        worker_id="USR-ASHA-RAMPUR-2",
        updates={"assigned_area_id": "AREA-562160-1"},
        performed_by="USR-ADMIN"
    )
    # Check audit log recorded
    logs = get_audit_logs(limit=5)
    reassigned_log = any(l["action"] == "AREA_REASSIGNED" and "AREA-562160-1" in (l.get("target_id") or l.get("details")) for l in logs)
    assert reassigned_log, f"Expected audit log for AREA_REASSIGNED. Found: {logs}"
    print("  PASS: Area successfully reassigned by Admin and logged in audit trail.")
    passed_count += 1

    # ------------------------------------------------------------------------
    # SCENARIO 10: Public search reflects updated assignment immediately
    # ------------------------------------------------------------------------
    print("\n[Scenario 10] Testing public search reflects updated assignment immediately...")
    res10 = find_asha_workers(village="Shantipura")
    assert len(res10) == 1, f"Expected 1 worker for Shantipura after reassignment, found {len(res10)}"
    assert res10[0]["badge_id"] == "ASHA-KA-MDY-002"
    assert "Anasuya" in res10[0]["full_name"]
    print(f"  PASS: Public search immediately returned newly assigned worker '{res10[0]['full_name']}' ({res10[0]['badge_id']}).")
    passed_count += 1

    print("\n" + "=" * 70)
    print(f"ALL {passed_count}/{total_count} SCENARIOS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
