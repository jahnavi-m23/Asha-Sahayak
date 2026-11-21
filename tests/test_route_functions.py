"""
Direct Route Handler Tests for Household & Member Edit / Delete
"""

import sys
import os
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from backend.database.crud import init_db, seed_database_if_empty
from backend.routes.households import (
    HouseholdRegistrationSchema,
    FamilyMemberSchema,
    create_household,
    update_household,
    remove_household,
    create_household_member,
    edit_household_member,
    remove_household_member,
    get_household
)

class TestRouteFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_database_if_empty(force=True)
        cls.worker_rampur = {
            "id": "USR-ASHA-RAMPUR",
            "username": "asha_rampur",
            "role": "asha_worker",
            "assigned_area_id": "AREA-571428-1",
            "assigned_pincode": "571428",
            "assigned_village": "Rampur"
        }
        cls.worker_kalyanpur = {
            "id": "USR-ASHA-KALYANPUR",
            "username": "asha_kalyanpur",
            "role": "asha_worker",
            "assigned_area_id": "AREA-571434-1",
            "assigned_pincode": "571434",
            "assigned_village": "Kalyanpur"
        }

    def test_routes_execution(self):
        # 1. Create household
        reg = HouseholdRegistrationSchema(
            area_id="AREA-571428-1",
            head_of_family="Route Test Head",
            address="House #101, Test Road",
            pincode="571428",
            village="Rampur",
            contact_number="9876543210",
            family_members=[
                FamilyMemberSchema(full_name="Route Test Head", age=45, gender="Male", relationship="Self / Head"),
                FamilyMemberSchema(full_name="Route Test Wife", age=40, gender="Female", relationship="Spouse")
            ]
        )
        res_created = create_household(reg, current_user=self.worker_rampur)
        hh_id = res_created["household"]["id"]
        hh_code = res_created["household"]["household_code"]
        self.assertEqual(res_created["member_count"], 2)

        # 2. Update household (Edit)
        reg_updated = HouseholdRegistrationSchema(
            area_id="AREA-571428-1",
            head_of_family="Route Test Head (Modified)",
            address="House #101, Renovated Wing, Test Road",
            pincode="571428",
            village="Rampur",
            contact_number="9876543210",
            family_members=[
                FamilyMemberSchema(full_name="Route Test Head (Modified)", age=45, gender="Male", relationship="Self / Head"),
                FamilyMemberSchema(full_name="Route Test Wife", age=41, gender="Female", relationship="Spouse")
            ]
        )
        res_edit = update_household(hh_id, reg_updated, current_user=self.worker_rampur)
        self.assertEqual(res_edit["household"]["head_of_family"], "Route Test Head (Modified)")
        self.assertEqual(res_edit["household"]["address"], "House #101, Renovated Wing, Test Road")

        # 3. Add individual member
        new_mem = FamilyMemberSchema(
            full_name="Baby Girl",
            age=1,
            gender="Female",
            relationship="Daughter",
            is_child_under_5=True,
            requires_immunization=True,
            immunization_due="Measles-1"
        )
        res_add = create_household_member(hh_id, new_mem, current_user=self.worker_rampur)
        self.assertEqual(res_add["member_count"], 3)
        baby = next(m for m in res_add["family_members"] if m["full_name"] == "Baby Girl")

        # 4. Edit individual member
        edit_mem = FamilyMemberSchema(
            full_name="Baby Girl Ananya",
            age=2,
            gender="Female",
            relationship="Daughter"
        )
        res_mem_edit = edit_household_member(hh_id, baby["id"], edit_mem, current_user=self.worker_rampur)
        ananya = next(m for m in res_mem_edit["family_members"] if m["id"] == baby["id"])
        self.assertEqual(ananya["full_name"], "Baby Girl Ananya")
        self.assertEqual(ananya["age"], 2)

        # 5. Unauthorized access check (Kalyanpur worker cannot edit Rampur household)
        with self.assertRaises(HTTPException) as cm:
            update_household(hh_id, reg_updated, current_user=self.worker_kalyanpur)
        self.assertEqual(cm.exception.status_code, 403)

        # 6. Delete member
        res_del_mem = remove_household_member(hh_id, baby["id"], current_user=self.worker_rampur)
        self.assertEqual(res_del_mem["status"], "success")
        self.assertEqual(res_del_mem["updated_details"]["member_count"], 2)

        # 7. Unauthorized delete check
        with self.assertRaises(HTTPException) as cm2:
            remove_household(hh_id, current_user=self.worker_kalyanpur)
        self.assertEqual(cm2.exception.status_code, 403)

        # 8. Delete household
        res_del_hh = remove_household(hh_id, current_user=self.worker_rampur)
        self.assertEqual(res_del_hh["status"], "success")

        # 9. Verify household not found
        with self.assertRaises(HTTPException) as cm3:
            get_household(hh_id, current_user=self.worker_rampur)
        self.assertEqual(cm3.exception.status_code, 404)

        print("Route Functions Test: All handlers tested successfully!")

if __name__ == "__main__":
    unittest.main()
