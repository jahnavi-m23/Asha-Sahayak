"""
Synthetic Demo Data for ASHA Sahayak
Seeds Users (RBAC), Geographical Areas, Households, Family Members with Health Profiles,
Surveys, Beneficiaries, Completed Visits, and Follow-ups.
All data is strictly synthetic and created for healthcare evaluation.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

def hash_password(password: str) -> str:
    salt = "a1b2c3d4e5f60718293a4b5c6d7e8f90"  # Deterministic salt for synthetic demo users
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000)
    return f"{salt}${key.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt, key = stored.split('$')
        computed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000)
        return secrets.compare_digest(computed.hex(), key)
    except Exception:
        return False

def get_enhanced_seed_data():
    now_iso = datetime.now().isoformat()
    today = datetime.now().date()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    two_days_ago = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    five_days_ago = (today - timedelta(days=5)).strftime("%Y-%m-%d")
    ten_days_ago = (today - timedelta(days=10)).strftime("%Y-%m-%d")

    three_days_later = (today + timedelta(days=3)).strftime("%Y-%m-%d")
    seven_days_later = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    fourteen_days_later = (today + timedelta(days=14)).strftime("%Y-%m-%d")
    overdue_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")

    # 1. Users (Role-Based Access Control)
    users = [
        {
            "id": "USR-ADMIN",
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "full_name": "Dr. Rajeshwar Rao (Medical Officer / Administrator)",
            "mobile": "98000-00001",
            "assigned_area_id": None,
            "badge_id": "MED-OFF-KA-001",
            "phc_name": "Kestur Primary Health Centre",
            "work_contact": "08232-245100",
            "is_verified": 1,
            "is_active": 1,
            "created_at": now_iso
        },
        {
            "id": "USR-ASHA-RAMPUR",
            "username": "asha_rampur",
            "password_hash": hash_password("asha123"),
            "role": "asha_worker",
            "full_name": "Sunita Devi (ASHA Worker - Rampur Sector 1)",
            "mobile": "98000-00002",
            "assigned_area_id": "AREA-571428-1",
            "badge_id": "ASHA-KA-MDY-001",
            "phc_name": "Kestur Primary Health Centre",
            "work_contact": "98000-00002",
            "is_verified": 1,
            "is_active": 1,
            "created_at": now_iso
        },
        {
            "id": "USR-ASHA-RAMPUR-2",
            "username": "asha_rampur_2",
            "password_hash": hash_password("asha123"),
            "role": "asha_worker",
            "full_name": "Anasuya Bai (ASHA Worker - Rampur Sector 2)",
            "mobile": "98000-00005",
            "assigned_area_id": "AREA-571428-2",
            "badge_id": "ASHA-KA-MDY-002",
            "phc_name": "Kestur Primary Health Centre",
            "work_contact": "98000-00005",
            "is_verified": 1,
            "is_active": 1,
            "created_at": now_iso
        },
        {
            "id": "USR-ASHA-KALYANPUR",
            "username": "asha_kalyanpur",
            "password_hash": hash_password("asha123"),
            "role": "asha_worker",
            "full_name": "Geetha Gowda (ASHA Worker - Kalyanpur)",
            "mobile": "98000-00003",
            "assigned_area_id": "AREA-571434-1",
            "badge_id": "ASHA-KA-MDY-003",
            "phc_name": "Kestur Primary Health Centre",
            "work_contact": "98000-00003",
            "is_verified": 1,
            "is_active": 1,
            "created_at": now_iso
        },
        {
            "id": "USR-SUPERVISOR",
            "username": "supervisor_maddur",
            "password_hash": hash_password("sup123"),
            "role": "health_supervisor",
            "full_name": "Venkatesh Murthy (Taluk Health Supervisor)",
            "mobile": "98000-00004",
            "assigned_area_id": None,
            "badge_id": "SUP-KA-MDY-010",
            "phc_name": "Maddur Taluk Health Office",
            "work_contact": "08232-245220",
            "is_verified": 1,
            "is_active": 1,
            "created_at": now_iso
        }
    ]

    # 2. Geographical Areas & Pincodes
    areas = [
        {
            "id": "AREA-571428-1",
            "state": "Karnataka",
            "district": "Mandya",
            "taluk": "Maddur",
            "village": "Rampur",
            "area_name": "Ward 4 - Anganwadi Center 2",
            "pincode": "571428",
            "phc_name": "Kestur Primary Health Centre",
            "assigned_worker_id": "USR-ASHA-RAMPUR",
            "latitude": 12.5847,
            "longitude": 77.0426,
            "created_at": now_iso
        },
        {
            "id": "AREA-571428-2",
            "state": "Karnataka",
            "district": "Mandya",
            "taluk": "Maddur",
            "village": "Rampur",
            "area_name": "Ward 2 & 3 - Colony Extension",
            "pincode": "571428",
            "phc_name": "Kestur Primary Health Centre",
            "assigned_worker_id": "USR-ASHA-RAMPUR-2",
            "latitude": 12.5880,
            "longitude": 77.0450,
            "created_at": now_iso
        },
        {
            "id": "AREA-571434-1",
            "state": "Karnataka",
            "district": "Mandya",
            "taluk": "Maddur",
            "village": "Kalyanpur",
            "area_name": "Ward 2 - Subcenter Colony",
            "pincode": "571434",
            "phc_name": "Kestur Primary Health Centre",
            "assigned_worker_id": "USR-ASHA-KALYANPUR",
            "latitude": 12.6120,
            "longitude": 77.0780,
            "created_at": now_iso
        },
        {
            "id": "AREA-562160-1",
            "state": "Karnataka",
            "district": "Ramanagara",
            "taluk": "Channapatna",
            "village": "Shantipura",
            "area_name": "Ward 1 - Main Village Temple Road",
            "pincode": "562160",
            "phc_name": "Channapatna Taluk Hospital",
            "assigned_worker_id": None,
            "latitude": 12.6510,
            "longitude": 77.2050,
            "created_at": now_iso
        }
    ]

    # 3. Households
    households = [
        {
            "id": "HH-571428-001",
            "household_code": "HH-571428-001",
            "area_id": "AREA-571428-1",
            "head_of_family": "Ramesh Gowda",
            "address": "House # 42, Near Maramma Temple, Rampur",
            "pincode": "571428",
            "village": "Rampur",
            "contact_number": "98765-11001",
            "house_type": "Pucca",
            "water_source": "Piped Water / Tap",
            "toilet_available": "Individual Household Latrine (IHHL)",
            "sanitation_facility": "Closed Drainage",
            "survey_status": "completed",
            "created_by_worker_id": "USR-ASHA-RAMPUR",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "HH-571428-002",
            "household_code": "HH-571428-002",
            "area_id": "AREA-571428-1",
            "head_of_family": "Basavaraju M",
            "address": "House # 78, Old Post Office Road, Rampur",
            "pincode": "571428",
            "village": "Rampur",
            "contact_number": "98765-11002",
            "house_type": "Semi-Pucca",
            "water_source": "Piped Water / Tap",
            "toilet_available": "Individual Household Latrine (IHHL)",
            "sanitation_facility": "Soak Pit",
            "survey_status": "completed",
            "created_by_worker_id": "USR-ASHA-RAMPUR",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "HH-571428-003",
            "household_code": "HH-571428-003",
            "area_id": "AREA-571428-1",
            "head_of_family": "Shivanna K",
            "address": "House # 105, East Ward 4, Rampur",
            "pincode": "571428",
            "village": "Rampur",
            "contact_number": "98765-11003",
            "house_type": "Kutcha",
            "water_source": "Borewell / Handpump",
            "toilet_available": "None / Open",
            "sanitation_facility": "Open Drain",
            "survey_status": "draft",
            "created_by_worker_id": "USR-ASHA-RAMPUR",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "HH-571434-001",
            "household_code": "HH-571434-001",
            "area_id": "AREA-571434-1",
            "head_of_family": "Manjunath Patil",
            "address": "Plot # 12, Subcenter Main Road, Kalyanpur",
            "pincode": "571434",
            "village": "Kalyanpur",
            "contact_number": "98765-22001",
            "house_type": "Pucca",
            "water_source": "Filter Plant / RO",
            "toilet_available": "Individual Household Latrine (IHHL)",
            "sanitation_facility": "Closed Drainage",
            "survey_status": "completed",
            "created_by_worker_id": "USR-ASHA-KALYANPUR",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "HH-571434-002",
            "household_code": "HH-571434-002",
            "area_id": "AREA-571434-1",
            "head_of_family": "Nagaraj Rao",
            "address": "House # 55, Kalyanpur Ward 2",
            "pincode": "571434",
            "village": "Kalyanpur",
            "contact_number": "98765-22002",
            "house_type": "Pucca",
            "water_source": "Piped Water / Tap",
            "toilet_available": "Individual Household Latrine (IHHL)",
            "sanitation_facility": "Closed Drainage",
            "survey_status": "completed",
            "created_by_worker_id": "USR-ASHA-KALYANPUR",
            "created_at": now_iso,
            "updated_at": now_iso
        }
    ]

    # 4. Family Members with Configurable Health Information
    members = [
        # Household 1 (Ramesh Gowda - Rampur)
        {
            "id": "MEM-101",
            "household_id": "HH-571428-001",
            "full_name": "Ramesh Gowda",
            "age": 48,
            "gender": "Male",
            "dob": "1978-05-12",
            "relationship": "Self / Head",
            "mobile": "98765-11001",
            "occupation": "Agriculture / Farmer",
            "education": "Secondary",
            "marital_status": "Married",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": None,
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "Hypertension", "current_medications": "Amlodipine 5mg",
            "recent_checkup_date": five_days_ago, "nutritional_status": "Normal",
            "special_needs": "Periodic BP monitoring at PHC",
            "created_at": now_iso, "updated_at": now_iso
        },
        {
            "id": "MEM-102",
            "household_id": "HH-571428-001",
            "full_name": "Lakshmi Gowda",
            "age": 44,
            "gender": "Female",
            "dob": "1982-08-20",
            "relationship": "Spouse",
            "mobile": "98765-11002",
            "occupation": "Homemaker & Dairy",
            "education": "Primary",
            "marital_status": "Married",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": None,
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": None,
            "recent_checkup_date": ten_days_ago, "nutritional_status": "Normal",
            "special_needs": None,
            "created_at": now_iso, "updated_at": now_iso
        },
        {
            "id": "MEM-103",
            "household_id": "HH-571428-001",
            "full_name": "Ningamma (Elderly Mother)",
            "age": 72,
            "gender": "Female",
            "dob": "1954-02-10",
            "relationship": "Mother",
            "mobile": None,
            "occupation": "Retired",
            "education": "Illiterate",
            "marital_status": "Widowed",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": None,
            "is_elderly": 1, "has_disability": 1, "disability_type": "Locomotor / Arthritis",
            "chronic_conditions": "Diabetes, Joint Pain", "current_medications": "Metformin 500mg",
            "recent_checkup_date": two_days_ago, "nutritional_status": "Normal",
            "special_needs": "Home visit required for NCD screening",
            "created_at": now_iso, "updated_at": now_iso
        },
        {
            "id": "MEM-104",
            "household_id": "HH-571428-001",
            "full_name": "Pavan Gowda",
            "age": 4,
            "gender": "Male",
            "dob": "2022-07-15",
            "relationship": "Grandchild",
            "mobile": None,
            "occupation": "Anganwadi Student",
            "education": "Primary",
            "marital_status": "Unmarried",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 1, "requires_immunization": 1, "immunization_due": "DPT Booster-1, OPV Booster",
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": "Vitamin A syrup",
            "recent_checkup_date": yesterday, "nutritional_status": "Normal",
            "special_needs": "Weight tracking at Anganwadi",
            "created_at": now_iso, "updated_at": now_iso
        },

        # Household 2 (Basavaraju M - Rampur, includes Lactating Mother Pooja Sharma BNF-2041)
        {
            "id": "MEM-201",
            "household_id": "HH-571428-002",
            "full_name": "Basavaraju M",
            "age": 27,
            "gender": "Male",
            "dob": "1999-04-18",
            "relationship": "Self / Head",
            "mobile": "98765-11004",
            "occupation": "Transport Operator",
            "education": "Higher Secondary",
            "marital_status": "Married",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": None,
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": None,
            "recent_checkup_date": ten_days_ago, "nutritional_status": "Normal",
            "special_needs": None,
            "created_at": now_iso, "updated_at": now_iso
        },
        {
            "id": "MEM-202",
            "household_id": "HH-571428-002",
            "full_name": "Pooja Sharma (BNF-2041)",
            "age": 22,
            "gender": "Female",
            "dob": "2004-10-05",
            "relationship": "Spouse",
            "mobile": "98765-XXXX1",
            "occupation": "Homemaker",
            "education": "Secondary",
            "marital_status": "Married",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 1, "lactating_child_age_months": 1,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": None,
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": "IFA & Calcium tablets",
            "recent_checkup_date": yesterday, "nutritional_status": "Normal",
            "special_needs": "PNC home visits Day 14, 21, 28",
            "created_at": now_iso, "updated_at": now_iso
        },
        {
            "id": "MEM-203",
            "household_id": "HH-571428-002",
            "full_name": "Baby Aarav (Newborn)",
            "age": 0,
            "gender": "Male",
            "dob": "2026-10-25",
            "relationship": "Son",
            "mobile": None,
            "occupation": "Infant",
            "education": "None",
            "marital_status": "Unmarried",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 1, "requires_immunization": 1, "immunization_due": "OPV-1, Pentavalent-1, Rotavirus-1",
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": None,
            "recent_checkup_date": yesterday, "nutritional_status": "Normal",
            "special_needs": "Birth weight 3.2 kg, routine HBNV care",
            "created_at": now_iso, "updated_at": now_iso
        },

        # Household 3 (Shivanna K - Draft survey)
        {
            "id": "MEM-301",
            "household_id": "HH-571428-003",
            "full_name": "Shivanna K",
            "age": 65,
            "gender": "Male",
            "dob": "1961-09-12",
            "relationship": "Self / Head",
            "mobile": "98765-11003",
            "occupation": "Daily Wage Laborer",
            "education": "Illiterate",
            "marital_status": "Married",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": None,
            "is_elderly": 1, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "Asthma", "current_medications": "Salbutamol Inhaler",
            "recent_checkup_date": None, "nutritional_status": "MAM",
            "special_needs": "Survey pending full family member verification",
            "created_at": now_iso, "updated_at": now_iso
        },

        # Household 4 (Manjunath Patil - Kalyanpur, includes Pregnant Woman Kavita Devi BNF-1082)
        {
            "id": "MEM-401",
            "household_id": "HH-571434-001",
            "full_name": "Manjunath Patil",
            "age": 31,
            "gender": "Male",
            "dob": "1995-03-14",
            "relationship": "Self / Head",
            "mobile": "98765-22001",
            "occupation": "Shopkeeper",
            "education": "Graduate & Above",
            "marital_status": "Married",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": None,
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": None,
            "recent_checkup_date": five_days_ago, "nutritional_status": "Normal",
            "special_needs": None,
            "created_at": now_iso, "updated_at": now_iso
        },
        {
            "id": "MEM-402",
            "household_id": "HH-571434-001",
            "full_name": "Kavita Devi (BNF-1082)",
            "age": 26,
            "gender": "Female",
            "dob": "2000-06-18",
            "relationship": "Spouse",
            "mobile": "98765-XXXX2",
            "occupation": "Teacher",
            "education": "Graduate & Above",
            "marital_status": "Married",
            "is_pregnant": 1, "pregnancy_trimester": "3rd Trimester",
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": "TT-2 booster due",
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": "IFA, Calcium, Albendazole",
            "recent_checkup_date": five_days_ago, "nutritional_status": "Normal",
            "special_needs": "32-week ANC follow-up, BP monitoring",
            "created_at": now_iso, "updated_at": now_iso
        },

        # Household 5 (Nagaraj Rao - Kalyanpur, includes infant Anita Verma BNF-5219)
        {
            "id": "MEM-501",
            "household_id": "HH-571434-002",
            "full_name": "Nagaraj Rao",
            "age": 29,
            "gender": "Male",
            "dob": "1997-11-09",
            "relationship": "Self / Head",
            "mobile": "98765-22002",
            "occupation": "Carpenter",
            "education": "Secondary",
            "marital_status": "Married",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": None,
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": None,
            "recent_checkup_date": ten_days_ago, "nutritional_status": "Normal",
            "special_needs": None,
            "created_at": now_iso, "updated_at": now_iso
        },
        {
            "id": "MEM-502",
            "household_id": "HH-571434-002",
            "full_name": "Anita Verma (BNF-5219)",
            "age": 24,
            "gender": "Female",
            "dob": "2002-01-14",
            "relationship": "Spouse",
            "mobile": "98765-XXXX5",
            "occupation": "Homemaker",
            "education": "Secondary",
            "marital_status": "Married",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 1, "lactating_child_age_months": 9,
            "is_child_under_5": 0, "requires_immunization": 0, "immunization_due": None,
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": None,
            "recent_checkup_date": yesterday, "nutritional_status": "Normal",
            "special_needs": "Mother of 9-month infant due for MR-1 vaccine",
            "created_at": now_iso, "updated_at": now_iso
        },
        {
            "id": "MEM-503",
            "household_id": "HH-571434-002",
            "full_name": "Baby Priya",
            "age": 1,
            "gender": "Female",
            "dob": "2025-11-20",
            "relationship": "Daughter",
            "mobile": None,
            "occupation": "Infant",
            "education": "None",
            "marital_status": "Unmarried",
            "is_pregnant": 0, "pregnancy_trimester": None,
            "is_lactating": 0, "lactating_child_age_months": None,
            "is_child_under_5": 1, "requires_immunization": 1, "immunization_due": "MR-1, JE-1, Vitamin-A",
            "is_elderly": 0, "has_disability": 0, "disability_type": None,
            "chronic_conditions": "None", "current_medications": None,
            "recent_checkup_date": yesterday, "nutritional_status": "Normal",
            "special_needs": "VHND immunization due next week",
            "created_at": now_iso, "updated_at": now_iso
        }
    ]

    # 5. Survey Audits
    surveys = [
        {
            "id": "SRV-571428-01",
            "household_id": "HH-571428-001",
            "worker_id": "USR-ASHA-RAMPUR",
            "survey_date": five_days_ago,
            "status": "completed",
            "remarks": "Survey completed. Child immunization and elderly health care advised.",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "SRV-571428-02",
            "household_id": "HH-571428-002",
            "worker_id": "USR-ASHA-RAMPUR",
            "survey_date": two_days_ago,
            "status": "completed",
            "remarks": "Newborn home visit and family profile registered. Exclusive breastfeeding counseling given.",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "SRV-571428-03",
            "household_id": "HH-571428-003",
            "worker_id": "USR-ASHA-RAMPUR",
            "survey_date": yesterday,
            "status": "draft",
            "remarks": "Draft survey saved. Head of family interviewed; waiting for remaining members.",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "SRV-571434-01",
            "household_id": "HH-571434-001",
            "worker_id": "USR-ASHA-KALYANPUR",
            "survey_date": five_days_ago,
            "status": "completed",
            "remarks": "Pregnant woman registration (32 weeks) confirmed. MCP card verified.",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "SRV-571434-02",
            "household_id": "HH-571434-002",
            "worker_id": "USR-ASHA-KALYANPUR",
            "survey_date": yesterday,
            "status": "completed",
            "remarks": "Infant due for 9-month immunization. Mother briefed on VHND schedule.",
            "created_at": now_iso,
            "updated_at": now_iso
        }
    ]

    # 6. Preserved Phase 3 Beneficiaries (Linked & Extended)
    beneficiaries = [
        {
            "beneficiary_id": "BNF-2041",
            "full_name": "Pooja Sharma (Synthetic)",
            "age_years": 22,
            "gender": "Female",
            "category": "Lactating Mother / Newborn",
            "village_ward": "Rampur - Ward 4",
            "contact_number": "98765-XXXX1",
            "notes": "Delivered baby boy at PHC Rampur. Postnatal home visits ongoing.",
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "beneficiary_id": "BNF-1082",
            "full_name": "Kavita Devi (Synthetic)",
            "age_years": 26,
            "gender": "Female",
            "category": "Pregnant Woman (ANC)",
            "village_ward": "Kalyanpur - Ward 2",
            "contact_number": "98765-XXXX2",
            "notes": "3rd Trimester (32 weeks). Needs regular IFA tablets & BP check.",
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "beneficiary_id": "BNF-3094",
            "full_name": "Meena Kumari (Synthetic)",
            "age_years": 19,
            "gender": "Female",
            "category": "Lactating Mother / Newborn",
            "village_ward": "Shantipura - Ward 1",
            "contact_number": "98765-XXXX3",
            "notes": "First-time mother. Needs counseling on exclusive breastfeeding.",
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "beneficiary_id": "BNF-4105",
            "full_name": "Sunita Patel (Synthetic)",
            "age_years": 28,
            "gender": "Female",
            "category": "Pregnant Woman (High Risk)",
            "village_ward": "Rampur - Ward 5",
            "contact_number": "98765-XXXX4",
            "notes": "Flagged for severe anemia (Hb 7.8 g/dL). Referred to CHC.",
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "beneficiary_id": "BNF-5219",
            "full_name": "Anita Verma (Synthetic)",
            "age_years": 24,
            "gender": "Female",
            "category": "Infant (9 Months)",
            "village_ward": "Kalyanpur - Ward 3",
            "contact_number": "98765-XXXX5",
            "notes": "Due for Measles-Rubella (MR-1) and Vitamin A dose 1.",
            "created_at": now_iso,
            "updated_at": now_iso,
        },
    ]

    # 7. Preserved Phase 3 Visits
    visits = [
        {
            "visit_id": "VIS-9001",
            "beneficiary_id": "BNF-1082",
            "visit_type": "ANC Home Checkup",
            "weight": "54.5 kg",
            "vaccinations_due": ["TT-2", "IFA Supplementation"],
            "next_visit_date": seven_days_later,
            "danger_signs": [],
            "referral_required": 0,
            "referral_facility": "Not Required",
            "referral_status": "Not Required",
            "confirmation_status": "confirmed",
            "submission_hash": "seed-hash-vis-9001",
            "visit_date": five_days_ago,
            "created_at": now_iso,
        },
        {
            "visit_id": "VIS-9002",
            "beneficiary_id": "BNF-4105",
            "visit_type": "High Risk ANC Visit",
            "weight": "49.0 kg",
            "vaccinations_due": [],
            "next_visit_date": three_days_later,
            "danger_signs": ["Severe Pallor", "Extreme Fatigue", "Breathlessness"],
            "referral_required": 1,
            "referral_facility": "Primary Health Centre (PHC) & CHC",
            "referral_status": "Pending PHC Referral",
            "confirmation_status": "confirmed",
            "submission_hash": "seed-hash-vis-9002",
            "visit_date": two_days_ago,
            "created_at": now_iso,
        },
        {
            "visit_id": "VIS-9003",
            "beneficiary_id": "BNF-5219",
            "visit_type": "Immunization Tracking Visit",
            "weight": "7.8 kg",
            "vaccinations_due": ["MR-1", "JE-1", "Vitamin-A"],
            "next_visit_date": fourteen_days_later,
            "danger_signs": [],
            "referral_required": 0,
            "referral_facility": "Not Required",
            "referral_status": "Not Required",
            "confirmation_status": "confirmed",
            "submission_hash": "seed-hash-vis-9003",
            "visit_date": yesterday,
            "created_at": now_iso,
        },
        {
            "visit_id": "VIS-9004",
            "beneficiary_id": "BNF-3094",
            "visit_type": "Newborn Home Visit (Day 3)",
            "weight": "2.8 kg",
            "vaccinations_due": ["BCG", "HepB-0"],
            "next_visit_date": overdue_date,
            "danger_signs": ["Mild Jaundice"],
            "referral_required": 1,
            "referral_facility": "PHC Shantipura",
            "referral_status": "Pending PHC Referral",
            "confirmation_status": "confirmed",
            "submission_hash": "seed-hash-vis-9004",
            "visit_date": ten_days_ago,
            "created_at": now_iso,
        },
    ]

    # 8. Preserved Phase 3 Follow-ups
    follow_ups = [
        {
            "followup_id": "FOL-8001",
            "visit_id": "VIS-9001",
            "beneficiary_id": "BNF-1082",
            "scheduled_date": seven_days_later,
            "status": "upcoming",
            "reason": "ANC follow-up: Blood Pressure monitoring and IFA compliance check",
            "worker_notes": "Beneficiary advised to keep diet rich in green leafy vegetables.",
            "updated_by": "ASHA-Rampur-1",
            "completed_at": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "followup_id": "FOL-8002",
            "visit_id": "VIS-9002",
            "beneficiary_id": "BNF-4105",
            "scheduled_date": three_days_later,
            "status": "upcoming",
            "reason": "URGENT PHC Referral Escort: Severe Anemia evaluation with Medical Officer",
            "worker_notes": "Husband contacted. Arranging 108/102 ambulance support if needed.",
            "updated_by": "ASHA-Rampur-1",
            "completed_at": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "followup_id": "FOL-8003",
            "visit_id": "VIS-9003",
            "beneficiary_id": "BNF-5219",
            "scheduled_date": fourteen_days_later,
            "status": "upcoming",
            "reason": "Village Health and Nutrition Day (VHND) immunization verification",
            "worker_notes": "Mother notified to bring Mother-Child Protection (MCP) card.",
            "updated_by": "ASHA-Kalyanpur-2",
            "completed_at": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        {
            "followup_id": "FOL-8004",
            "visit_id": "VIS-9004",
            "beneficiary_id": "BNF-3094",
            "scheduled_date": overdue_date,
            "status": "overdue",
            "reason": "Post-natal day 7 visit & neonatal jaundice observation",
            "worker_notes": "Worker scheduled visit but mother was temporarily visiting maternal home.",
            "updated_by": "ASHA-Shantipura-1",
            "completed_at": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        },
    ]

    # 9. Worker to Area Assignments
    assignments = [
        {
            "id": "WAA-001",
            "worker_id": "USR-ASHA-RAMPUR",
            "area_id": "AREA-571428-1",
            "is_primary": 1,
            "assigned_at": now_iso
        },
        {
            "id": "WAA-002",
            "worker_id": "USR-ASHA-RAMPUR-2",
            "area_id": "AREA-571428-2",
            "is_primary": 1,
            "assigned_at": now_iso
        },
        {
            "id": "WAA-003",
            "worker_id": "USR-ASHA-KALYANPUR",
            "area_id": "AREA-571434-1",
            "is_primary": 1,
            "assigned_at": now_iso
        }
    ]

    # 10. Initial Audit Logs
    audit_logs = [
        {
            "id": "AUD-001",
            "action": "WORKER_REGISTERED",
            "performed_by": "USR-ADMIN",
            "target_entity": "USER",
            "target_id": "USR-ASHA-RAMPUR",
            "details": "Registered Sunita Devi (ASHA-KA-MDY-001) for Rampur Ward 4",
            "created_at": ten_days_ago + "T09:00:00"
        },
        {
            "id": "AUD-002",
            "action": "WORKER_REGISTERED",
            "performed_by": "USR-ADMIN",
            "target_entity": "USER",
            "target_id": "USR-ASHA-RAMPUR-2",
            "details": "Registered Anasuya Bai (ASHA-KA-MDY-002) for Rampur Ward 2 & 3",
            "created_at": five_days_ago + "T10:30:00"
        },
        {
            "id": "AUD-003",
            "action": "WORKER_REGISTERED",
            "performed_by": "USR-ADMIN",
            "target_entity": "USER",
            "target_id": "USR-ASHA-KALYANPUR",
            "details": "Registered Geetha Gowda (ASHA-KA-MDY-003) for Kalyanpur Subcenter",
            "created_at": ten_days_ago + "T11:15:00"
        }
    ]

    return users, areas, households, members, surveys, beneficiaries, visits, follow_ups, assignments, audit_logs

def get_synthetic_seed_data():
    """Compatibility wrapper for Phase 3 seed loader."""
    users, areas, households, members, surveys, beneficiaries, visits, follow_ups, *extra = get_enhanced_seed_data()
    return beneficiaries, visits, follow_ups
