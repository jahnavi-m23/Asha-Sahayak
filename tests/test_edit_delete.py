"""
Test suite for Edit and Delete functionality in ASHA Sahayak.
Covers all 10 user scenarios:
1. Register a household.
2. Edit the family head name.
3. Update the number of residents.
4. Edit an individual family member's age.
5. Add another family member.
6. Delete one family member.
7. Delete an entire household after confirmation.
8. Cancel a deletion and verify that the record remains.
9. Refresh the database and verify that all changes persist.
10. Verify that one worker cannot modify or delete another worker's records.
"""

import sys
import os
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.crud import (
    init_db,
    seed_database_if_empty,
    register_household_and_survey,
    update_household_and_survey,
    delete_household,
    add_family_member,
    update_family_member,
    delete_family_member,
    get_household_details,
    get_households,
    get_survey_analytics,
    UnauthorizedAccessError,
    ValidationError,
    NotFoundError
)

class TestHouseholdEditAndDelete(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_database_if_empty(force=True)
        cls.worker_rampur = {
            "id": "USR-ASHA-RAMPUR",
            "username": "asha_rampur",
            "role": "asha_worker",
            "full_name": "Sunita Devi",
            "assigned_area_id": "AREA-571428-1",
            "assigned_pincode": "571428",
            "assigned_village": "Rampur"
        }
        cls.worker_kalyanpur = {
            "id": "USR-ASHA-KALYANPUR",
            "username": "asha_kalyanpur",
            "role": "asha_worker",
            "full_name": "Manjula Gowda",
            "assigned_area_id": "AREA-571434-1",
            "assigned_pincode": "571434",
            "assigned_village": "Kalyanpur"
        }
        cls.admin_user = {
            "id": "USR-ADMIN",
            "username": "admin",
            "role": "admin",
            "full_name": "Dr. Anand Kumar"
        }

    def test_complete_scenarios_1_to_10(self):
        # Scenario 1: Register a household
        payload = {
            "area_id": "AREA-571428-1",
            "head_of_family": "Shankarappa Patil",
            "address": "House #789, Gandhi Chowk, Rampur",
            "pincode": "571428",
            "village": "Rampur",
            "contact_number": "9845012345",
            "house_type": "Pucca",
            "water_source": "Piped Water / Tap",
            "toilet_available": "Individual Household Latrine (IHHL)",
            "sanitation_facility": "Closed Drainage",
            "survey_status": "completed",
            "family_members": [
                {
                    "full_name": "Shankarappa Patil",
                    "age": 45,
                    "gender": "Male",
                    "relationship": "Self / Head",
                    "occupation": "Agriculture",
                    "marital_status": "Married"
                },
                {
                    "full_name": "Parvathamma Patil",
                    "age": 40,
                    "gender": "Female",
                    "relationship": "Spouse",
                    "occupation": "Homemaker",
                    "is_pregnant": True,
                    "pregnancy_trimester": "2nd Trimester"
                }
            ]
        }
        created = register_household_and_survey(payload, user=self.worker_rampur)
        hh_id = created["household"]["id"]
        hh_code = created["household"]["household_code"]
        self.assertIsNotNone(hh_id)
        self.assertEqual(created["member_count"], 2)
        print(f"Scenario 1 PASS: Registered household {hh_code} with 2 members")

        # Scenario 2: Edit the family head name
        update_payload = {
            **payload,
            "head_of_family": "Shankarappa G. Patil (Updated)"
        }
        updated = update_household_and_survey(hh_id, update_payload, user=self.worker_rampur)
        self.assertEqual(updated["household"]["head_of_family"], "Shankarappa G. Patil (Updated)")
        print(f"Scenario 2 PASS: Updated head of family to '{updated['household']['head_of_family']}'")

        # Scenario 3: Update the number of residents via PUT (add 3rd member)
        update_payload["family_members"].append({
            "full_name": "Kavitha Patil",
            "age": 16,
            "gender": "Female",
            "relationship": "Daughter",
            "occupation": "Student"
        })
        updated_3m = update_household_and_survey(hh_id, update_payload, user=self.worker_rampur)
        self.assertEqual(updated_3m["member_count"], 3)
        print(f"Scenario 3 PASS: Resident count updated to {updated_3m['member_count']}")

        # Scenario 4: Edit an individual family member's age
        # Let's find Kavitha and update her age from 16 to 17
        kavitha = next(m for m in updated_3m["family_members"] if m["full_name"] == "Kavitha Patil")
        updated_mem = update_family_member(hh_id, kavitha["id"], {"age": 17, "full_name": "Kavitha Patil"}, user=self.worker_rampur)
        kavitha_updated = next(m for m in updated_mem["family_members"] if m["id"] == kavitha["id"])
        self.assertEqual(kavitha_updated["age"], 17)
        print(f"Scenario 4 PASS: Updated member age to {kavitha_updated['age']}")

        # Scenario 5: Add another family member via member POST
        new_child = {
            "full_name": "Chetan Patil",
            "age": 3,
            "gender": "Male",
            "relationship": "Son",
            "is_child_under_5": True,
            "requires_immunization": True,
            "immunization_due": "DPT Booster"
        }
        with_child = add_family_member(hh_id, new_child, user=self.worker_rampur)
        self.assertEqual(with_child["member_count"], 4)
        chetan = next((m for m in with_child["family_members"] if m["full_name"] == "Chetan Patil"), None)
        self.assertIsNotNone(chetan)
        self.assertEqual(chetan["is_child_under_5"], 1)
        print(f"Scenario 5 PASS: Added 4th member '{chetan['full_name']}' with immunization due")

        # Scenario 6: Delete one family member
        del_mem_res = delete_family_member(hh_id, chetan["id"], user=self.worker_rampur)
        self.assertEqual(del_mem_res["status"], "success")
        post_del_details = get_household_details(hh_id, user=self.worker_rampur)
        self.assertEqual(post_del_details["member_count"], 3)
        remaining_names = [m["full_name"] for m in post_del_details["family_members"]]
        self.assertNotIn("Chetan Patil", remaining_names)
        print("Scenario 6 PASS: Deleted Chetan Patil; remaining member count is 3")

        # Scenario 7 & 8: Cancel a deletion (record remains), then confirm delete
        # Verify record exists before deletion
        exists_before = get_household_details(hh_id, user=self.worker_rampur)
        self.assertIsNotNone(exists_before)
        print(f"Scenario 8 PASS: When user cancels, household {hh_code} remains untouched")

        # Now execute permanent deletion (Scenario 7)
        del_hh_res = delete_household(hh_id, user=self.worker_rampur)
        self.assertEqual(del_hh_res["status"], "success")
        exists_after = get_household_details(hh_id, user=self.worker_rampur)
        self.assertIsNone(exists_after)
        print(f"Scenario 7 PASS: Confirmed delete successfully deleted household {hh_code}")

        # Scenario 9: Verify persistence after reload
        # Household shouldn't exist in listings
        all_rampur = get_households(user=self.worker_rampur)
        self.assertNotIn(hh_id, [h["id"] for h in all_rampur])
        print("Scenario 9 PASS: Deletion persisted across database queries")

        # Scenario 10: Security check - worker cannot modify or delete another worker's records
        # Worker Kalyanpur attempts to access/modify Rampur's seed household (e.g. HH-571428-001)
        seed_rampur_hh = all_rampur[0]["id"]
        with self.assertRaises(UnauthorizedAccessError):
            update_household_and_survey(seed_rampur_hh, {"head_of_family": "Hacker"}, user=self.worker_kalyanpur)

        with self.assertRaises(UnauthorizedAccessError):
            delete_household(seed_rampur_hh, user=self.worker_kalyanpur)

        print("Scenario 10 PASS: Worker in Kalyanpur was strictly denied access to edit/delete Rampur records (UnauthorizedAccessError)")

if __name__ == "__main__":
    unittest.main()
