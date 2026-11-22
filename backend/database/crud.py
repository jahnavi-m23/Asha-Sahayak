"""
Database CRUD Operations for ASHA Sahayak
Handles secure persistence, RBAC authentication, area-based scoping,
family and household surveys, member health tracking, duplicate prevention,
Phase 2/3 visit confirmations, and comprehensive healthcare analytics.
"""

import json
import hashlib
import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

from .connection import get_db
from .models import CREATE_TABLES_SQL, CREATE_MIGRATION_INDEXES_SQL
from .seed_data import get_enhanced_seed_data, verify_password, hash_password
from .validators import validate_confirmed_visit_payload

class DatabaseError(Exception):
    """Base database exception."""
    pass

class DuplicateVisitError(DatabaseError):
    """Raised when a duplicate visit submission is detected."""
    pass

class DuplicateHouseholdError(DatabaseError):
    """Raised when a duplicate household is registered."""
    pass

class ValidationError(DatabaseError):
    """Raised when incoming visit data fails validation."""
    pass

class NotFoundError(DatabaseError):
    """Raised when an entity is not found."""
    pass

class UnauthorizedAccessError(DatabaseError):
    """Raised when worker attempts unauthorized cross-area access."""
    pass

def init_db():
    """Initializes SQLite database tables and indexes with safe schema migrations."""
    with get_db() as conn:
        conn.executescript(CREATE_TABLES_SQL)
        alter_columns = [
            ("users", "badge_id TEXT"),
            ("users", "phc_name TEXT DEFAULT 'Primary Health Centre'"),
            ("users", "work_contact TEXT"),
            ("users", "is_verified INTEGER DEFAULT 1"),
            ("users", "is_active INTEGER DEFAULT 1"),
            ("users", "updated_at TEXT"),
            ("areas", "phc_name TEXT DEFAULT 'Kestur Primary Health Centre'"),
            ("areas", "latitude REAL"),
            ("areas", "longitude REAL"),
            ("areas", "updated_at TEXT"),
            ("visits", "beneficiary_name TEXT"),
            ("visits", "age INTEGER"),
            ("visits", "blood_pressure TEXT"),
            ("visits", "gestational_age TEXT"),
            ("visits", "symptoms_reported TEXT"),
            ("visits", "negated_symptoms TEXT"),
            ("visits", "raw_transcript TEXT"),
            ("visits", "worker_id TEXT"),
        ]
        for tbl, col_def in alter_columns:
            try:
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col_def}")
            except Exception:
                pass
        try:
            conn.executescript(CREATE_MIGRATION_INDEXES_SQL)
        except Exception:
            pass

def seed_database_if_empty(force: bool = False):
    """
    Seeds the SQLite database with complete synthetic demo data:
    Users, Areas, Households, Family Members, Surveys, Beneficiaries, Visits, Follow-ups,
    Worker Area Assignments, and Audit Logs.
    """
    init_db()
    with get_db() as conn:
        # Check if users table is populated
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        has_worker_2 = conn.execute("SELECT COUNT(*) FROM users WHERE id = 'USR-ASHA-RAMPUR-2'").fetchone()[0]
        needs_user_update = (user_count == 0 or force or has_worker_2 == 0)

        if needs_user_update:
            if force:
                conn.execute("DELETE FROM surveys")
                conn.execute("DELETE FROM family_members")
                conn.execute("DELETE FROM households")
                conn.execute("DELETE FROM worker_area_assignments")
                conn.execute("DELETE FROM audit_logs")
                conn.execute("DELETE FROM areas")
                conn.execute("DELETE FROM users")
                conn.execute("DELETE FROM follow_ups")
                conn.execute("DELETE FROM visits")
                conn.execute("DELETE FROM beneficiaries")

            seed_res = get_enhanced_seed_data()
            users = seed_res[0]
            areas = seed_res[1]
            households = seed_res[2]
            members = seed_res[3]
            surveys = seed_res[4]
            beneficiaries = seed_res[5]
            visits = seed_res[6]
            follow_ups = seed_res[7]
            assignments = seed_res[8] if len(seed_res) > 8 else []
            audit_logs = seed_res[9] if len(seed_res) > 9 else []

            # 1. Users
            for u in users:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO users 
                    (id, username, password_hash, role, full_name, mobile, assigned_area_id,
                     badge_id, phc_name, work_contact, is_verified, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (u["id"], u["username"], u["password_hash"], u["role"], u["full_name"], u["mobile"], u.get("assigned_area_id"),
                     u.get("badge_id"), u.get("phc_name", "Primary Health Centre"), u.get("work_contact", u.get("mobile")),
                     u.get("is_verified", 1), u.get("is_active", 1), u["created_at"], u.get("updated_at", u["created_at"]))
                )

            # 2. Areas
            for a in areas:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO areas 
                    (id, state, district, taluk, village, area_name, pincode, phc_name, assigned_worker_id, latitude, longitude, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (a["id"], a["state"], a["district"], a["taluk"], a["village"], a["area_name"], a["pincode"],
                     a.get("phc_name", "Kestur Primary Health Centre"), a.get("assigned_worker_id"),
                     a.get("latitude"), a.get("longitude"), a["created_at"], a.get("updated_at", a["created_at"]))
                )

            # Assignments
            for waa in assignments:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO worker_area_assignments (id, worker_id, area_id, is_primary, assigned_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (waa["id"], waa["worker_id"], waa["area_id"], waa.get("is_primary", 1), waa["assigned_at"])
                )

            # Audit logs
            for al in audit_logs:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO audit_logs (id, action, performed_by, target_entity, target_id, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (al["id"], al["action"], al["performed_by"], al.get("target_entity"), al.get("target_id"), al.get("details"), al["created_at"])
                )

            # Check if households need seeding
            hh_count = conn.execute("SELECT COUNT(*) FROM households").fetchone()[0]
            if hh_count == 0 or force:
                # 3. Households
                for h in households:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO households 
                        (id, household_code, area_id, head_of_family, address, pincode, village, contact_number,
                         house_type, water_source, toilet_available, sanitation_facility, survey_status,
                         created_by_worker_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (h["id"], h["household_code"], h["area_id"], h["head_of_family"], h["address"], h["pincode"],
                         h["village"], h["contact_number"], h["house_type"], h["water_source"], h["toilet_available"],
                         h["sanitation_facility"], h["survey_status"], h["created_by_worker_id"], h["created_at"], h["updated_at"])
                    )

                # 4. Family Members with Health Data
                for m in members:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO family_members
                        (id, household_id, full_name, age, gender, dob, relationship, mobile, occupation, education,
                         marital_status, is_pregnant, pregnancy_trimester, is_lactating, lactating_child_age_months,
                         is_child_under_5, requires_immunization, immunization_due, is_elderly, has_disability,
                         disability_type, chronic_conditions, current_medications, recent_checkup_date,
                         nutritional_status, special_needs, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (m["id"], m["household_id"], m["full_name"], m["age"], m["gender"], m["dob"], m["relationship"],
                         m["mobile"], m["occupation"], m["education"], m["marital_status"], m["is_pregnant"],
                         m["pregnancy_trimester"], m["is_lactating"], m["lactating_child_age_months"], m["is_child_under_5"],
                         m["requires_immunization"], m["immunization_due"], m["is_elderly"], m["has_disability"],
                         m["disability_type"], m["chronic_conditions"], m["current_medications"], m["recent_checkup_date"],
                         m["nutritional_status"], m["special_needs"], m["created_at"], m["updated_at"])
                    )

                # 5. Surveys
                for s in surveys:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO surveys (id, household_id, worker_id, survey_date, status, remarks, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (s["id"], s["household_id"], s["worker_id"], s["survey_date"], s["status"], s["remarks"], s["created_at"], s["updated_at"])
                    )

                # 6. Beneficiaries (Preserved)
                for b in beneficiaries:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO beneficiaries 
                        (beneficiary_id, full_name, age_years, gender, category, village_ward, contact_number, notes, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (b["beneficiary_id"], b["full_name"], b["age_years"], b["gender"], b["category"],
                         b["village_ward"], b["contact_number"], b["notes"], b["created_at"], b["updated_at"])
                    )

                # 7. Visits (Preserved)
                for v in visits:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO visits 
                        (visit_id, beneficiary_id, visit_type, weight, vaccinations_due, next_visit_date, 
                         danger_signs, referral_required, referral_facility, referral_status, 
                         confirmation_status, submission_hash, visit_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (v["visit_id"], v["beneficiary_id"], v["visit_type"], v["weight"], json.dumps(v["vaccinations_due"]),
                         v["next_visit_date"], json.dumps(v["danger_signs"]), v["referral_required"], v["referral_facility"],
                         v["referral_status"], v["confirmation_status"], v["submission_hash"], v["visit_date"], v["created_at"])
                    )

                # 8. Follow-ups (Preserved)
                for f in follow_ups:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO follow_ups 
                        (followup_id, visit_id, beneficiary_id, scheduled_date, status, reason, 
                         worker_notes, updated_by, completed_at, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (f["followup_id"], f["visit_id"], f["beneficiary_id"], f["scheduled_date"], f["status"],
                         f["reason"], f["worker_notes"], f["updated_by"], f["completed_at"], f["created_at"], f["updated_at"])
                    )


# ============================================================================
# AUTHENTICATION & ACCESS CONTROL CRUD
# ============================================================================

def authenticate_user(username_or_badge: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticates username, badge_id, or user ID and password against users table."""
    with get_db() as conn:
        key = username_or_badge.strip()
        row = conn.execute(
            """
            SELECT u.*, a.pincode as assigned_pincode, a.village as assigned_village, a.area_name as assigned_area_name
            FROM users u
            LEFT JOIN areas a ON u.assigned_area_id = a.id
            WHERE LOWER(u.username) = LOWER(?) OR LOWER(COALESCE(u.badge_id, '')) = LOWER(?) OR LOWER(u.id) = LOWER(?)
            """,
            (key, key, key)
        ).fetchone()

        if not row:
            return None

        # Check account activation status
        if row["is_active"] is not None and int(row["is_active"]) == 0:
            return None

        if verify_password(password, row["password_hash"]):
            user_data = dict(row)
            user_data.pop("password_hash", None)
            return user_data
        return None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves user profile and assigned area details."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT u.*, a.pincode as assigned_pincode, a.village as assigned_village, a.area_name as assigned_area_name
            FROM users u
            LEFT JOIN areas a ON u.assigned_area_id = a.id
            WHERE u.id = ?
            """,
            (user_id,)
        ).fetchone()
        if row:
            d = dict(row)
            d.pop("password_hash", None)
            return d
        return None

def get_all_users() -> List[Dict[str, Any]]:
    """Lists users for administration."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT u.id, u.username, u.role, u.full_name, u.mobile, u.assigned_area_id,
                   a.village as assigned_village, a.pincode as assigned_pincode, a.area_name
            FROM users u
            LEFT JOIN areas a ON u.assigned_area_id = a.id
            ORDER BY u.role, u.full_name
            """
        ).fetchall()
        return [dict(r) for r in rows]


# ============================================================================
# GEOGRAPHICAL AREAS CRUD
# ============================================================================

def get_areas(user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Lists geographical areas.
    If user is an ASHA worker, shows only her assigned area.
    If user is Administrator or Supervisor, shows all areas.
    """
    with get_db() as conn:
        query = """
            SELECT a.*, u.full_name as assigned_worker_name,
                   (SELECT COUNT(*) FROM households WHERE area_id = a.id) as total_households
            FROM areas a
            LEFT JOIN users u ON a.assigned_worker_id = u.id
        """
        params = []
        if user and user.get("role") == "asha_worker" and user.get("assigned_area_id"):
            query += " WHERE a.id = ?"
            params.append(user["assigned_area_id"])

        query += " ORDER BY a.district, a.taluk, a.village"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def create_area(data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new geographical area record."""
    area_id = f"AREA-{data['pincode']}-{uuid.uuid4().hex[:4].upper()}"
    now_iso = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO areas (id, state, district, taluk, village, area_name, pincode, assigned_worker_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (area_id, data.get("state", "Karnataka"), data["district"], data["taluk"],
             data["village"], data["area_name"], str(data["pincode"]), data.get("assigned_worker_id"), now_iso)
        )
        return get_area_by_id(area_id)

def get_area_by_id(area_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM areas WHERE id = ?", (area_id,)).fetchone()
        return dict(row) if row else None


# ============================================================================
# HOUSEHOLDS & FAMILY MEMBERS CRUD (SCOPED ACCESS)
# ============================================================================

def check_worker_area_authorization(user: Dict[str, Any], area_id: str):
    """
    Strict Area and Pincode Access Check:
    ASHA workers can only access households belonging to their designated area.
    """
    if user.get("role") == "admin" or user.get("role") == "health_supervisor":
        return True
    
    assigned_area = user.get("assigned_area_id")
    if not assigned_area or assigned_area != area_id:
        raise UnauthorizedAccessError(
            f"Access Denied: You are only authorized to access households in your assigned area ({user.get('assigned_area_name') or assigned_area})."
        )
    return True

def get_households(
    user: Optional[Dict[str, Any]] = None,
    pincode: Optional[str] = None,
    village: Optional[str] = None,
    area_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Retrieves households with area-based scoping.
    ASHA workers are strictly restricted to their assigned area / pincode.
    """
    with get_db() as conn:
        query = """
            SELECT h.*, a.area_name, a.district, a.taluk, u.full_name as worker_name,
                   (SELECT COUNT(*) FROM family_members WHERE household_id = h.id) as member_count,
                   (SELECT COUNT(*) FROM family_members WHERE household_id = h.id AND is_pregnant = 1) as pregnant_count,
                   (SELECT COUNT(*) FROM family_members WHERE household_id = h.id AND is_child_under_5 = 1) as children_under_5_count,
                   (SELECT COUNT(*) FROM family_members WHERE household_id = h.id AND is_elderly = 1) as elderly_count
            FROM households h
            LEFT JOIN areas a ON h.area_id = a.id
            LEFT JOIN users u ON h.created_by_worker_id = u.id
            WHERE 1=1
        """
        params = []

        # Role-based restriction: ASHA worker only sees her assigned area or households created by her
        if user and user.get("role") == "asha_worker":
            assigned_area = user.get("assigned_area_id")
            if assigned_area:
                query += " AND (h.area_id = ? OR h.created_by_worker_id = ?)"
                params.extend([assigned_area, user.get("id")])

        if area_id:
            query += " AND h.area_id = ?"
            params.append(area_id)
        if pincode:
            query += " AND h.pincode = ?"
            params.append(pincode.strip())
        if village:
            query += " AND h.village LIKE ?"
            params.append(f"%{village.strip()}%")
        if status:
            query += " AND h.survey_status = ?"
            params.append(status.strip())
        if search:
            s = f"%{search.strip()}%"
            query += " AND (h.household_code LIKE ? OR h.head_of_family LIKE ? OR h.address LIKE ?)"
            params.extend([s, s, s])

        query += " ORDER BY h.household_code ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["address_line"] = d.get("address")
            d["drinking_water_source"] = d.get("water_source")
            d["toilet_facility"] = bool(d.get("toilet_available") and "none" not in str(d.get("toilet_available")).lower())
            result.append(d)
        return result

def get_household_details(household_id: str, user: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves complete household profile with all individual family members,
    health information, and previous survey history.
    """
    with get_db() as conn:
        h_row = conn.execute(
            """
            SELECT h.*, a.area_name, a.district, a.taluk, u.full_name as worker_name
            FROM households h
            LEFT JOIN areas a ON h.area_id = a.id
            LEFT JOIN users u ON h.created_by_worker_id = u.id
            WHERE h.id = ?
            """,
            (household_id,)
        ).fetchone()

        if not h_row:
            return None

        household = dict(h_row)

        # Scoping check
        if user and user.get("role") == "asha_worker":
            check_worker_area_authorization(user, household["area_id"])

        # Fetch family members
        m_rows = conn.execute(
            "SELECT * FROM family_members WHERE household_id = ? ORDER BY relationship = 'Self / Head' DESC, age DESC",
            (household_id,)
        ).fetchall()
        members = [dict(m) for m in m_rows]

        # Fetch survey history
        s_rows = conn.execute(
            """
            SELECT s.*, u.full_name as worker_name
            FROM surveys s
            LEFT JOIN users u ON s.worker_id = u.id
            WHERE s.household_id = ?
            ORDER BY s.survey_date DESC
            """,
            (household_id,)
        ).fetchall()
        surveys = [dict(s) for s in s_rows]

        return {
            "id": household.get("id"),
            "household_code": household.get("household_code"),
            "head_of_family": household.get("head_of_family"),
            "village": household.get("village"),
            "pincode": household.get("pincode"),
            "household": household,
            "family_members": members,
            "member_count": len(members),
            "surveys": surveys
        }

def register_household_and_survey(payload: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registers a new household, adds family members with health info,
    and creates the initial survey record.
    Prevents duplicate household registrations.
    """
    head_of_family = str(payload.get("head_of_family", "")).strip()
    address = str(payload.get("address", "")).strip()
    pincode = str(payload.get("pincode", "")).strip()
    village = str(payload.get("village", "")).strip()

    if not head_of_family or not address or not pincode:
        raise ValidationError("Head of family, address, and PIN code are required.")

    now_iso = datetime.now().isoformat()
    area_id = payload.get("area_id") or user.get("assigned_area_id")

    with get_db() as conn:
        # If area_id is missing, find or auto-create matching area
        if not area_id:
            match = conn.execute(
                "SELECT id FROM areas WHERE pincode = ? OR village = ? LIMIT 1",
                (pincode, village)
            ).fetchone()
            if match:
                area_id = match[0]
            else:
                area_id = f"AREA-{pincode or '571428'}-{uuid.uuid4().hex[:4].upper()}"
                conn.execute(
                    """
                    INSERT INTO areas (id, state, district, taluk, village, area_name, pincode, assigned_worker_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (area_id, "Karnataka", "Mandya", "Maddur", village or "Rampur", f"{village or 'Rampur'} Field Area", pincode or "571428", user.get("id"), now_iso)
                )

        # Validate worker authorization (Admins & Supervisors can register anywhere)
        if user.get("role") == "asha_worker":
            check_worker_area_authorization(user, area_id)

        # Duplicate detection: check if identical head + address in same village
        dup = conn.execute(
            "SELECT id, household_code FROM households WHERE LOWER(head_of_family) = LOWER(?) AND LOWER(address) = LOWER(?) AND pincode = ?",
            (head_of_family, address, pincode)
        ).fetchone()

        if dup:
            raise DuplicateHouseholdError(
                f"Duplicate Household Warning: A household with head '{head_of_family}' at address '{address}' already exists ({dup['household_code']})."
            )

        # Check duplicate household code if explicitly provided
        if payload.get("household_code"):
            household_code = payload["household_code"]
            dup_code = conn.execute("SELECT id FROM households WHERE household_code = ?", (household_code,)).fetchone()
            if dup_code:
                raise DuplicateHouseholdError(f"Duplicate Household Warning: A household with code '{household_code}' already exists.")
        else:
            # Generate sequential household code
            seq_row = conn.execute("SELECT COUNT(*) FROM households WHERE pincode = ?", (pincode,)).fetchone()
            next_seq = (seq_row[0] or 0) + 1
            household_code = f"HH-{pincode}-{next_seq:03d}"

        household_id = f"HH-{uuid.uuid4().hex[:8].upper()}"

        survey_status = payload.get("survey_status", "completed")

        conn.execute(
            """
            INSERT INTO households
            (id, household_code, area_id, head_of_family, address, pincode, village, contact_number,
             house_type, water_source, toilet_available, sanitation_facility, survey_status,
             created_by_worker_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                household_id,
                household_code,
                area_id,
                head_of_family,
                address,
                pincode,
                village,
                payload.get("contact_number"),
                payload.get("house_type", "Pucca"),
                payload.get("water_source", "Piped Water / Tap"),
                payload.get("toilet_available", "Individual Household Latrine (IHHL)"),
                payload.get("sanitation_facility", "Closed Drainage"),
                survey_status,
                user["id"],
                now_iso,
                now_iso
            )
        )

        # Insert family members
        members_data = payload.get("family_members", [])
        if not members_data:
            members_data = [{
                "full_name": head_of_family,
                "age": 35,
                "gender": "Male",
                "relationship": "Self / Head",
                "mobile": payload.get("contact_number"),
                "occupation": "Agriculture",
                "education": "Secondary",
                "marital_status": "Married"
            }]

        for m in members_data:
            mem_id = f"MEM-{uuid.uuid4().hex[:8].upper()}"
            raw_age = m.get("age", 0)
            try:
                age = int(raw_age) if raw_age is not None and str(raw_age).strip() != "" else 0
            except (ValueError, TypeError):
                age = 0
            is_elderly = 1 if (age >= 60 or m.get("is_elderly")) else 0
            is_child_under_5 = 1 if (age < 5 or m.get("is_child_under_5")) else 0
            mem_name = str(m.get("full_name") or "").strip() or f"{head_of_family}'s Dependent"

            conn.execute(
                """
                INSERT INTO family_members
                (id, household_id, full_name, age, gender, dob, relationship, mobile, occupation, education,
                 marital_status, is_pregnant, pregnancy_trimester, is_lactating, lactating_child_age_months,
                 is_child_under_5, requires_immunization, immunization_due, is_elderly, has_disability,
                 disability_type, chronic_conditions, current_medications, recent_checkup_date,
                 nutritional_status, special_needs, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mem_id,
                    household_id,
                    mem_name,
                    age,
                    m.get("gender", "Female"),
                    m.get("dob"),
                    m.get("relationship", "Other"),
                    m.get("mobile"),
                    m.get("occupation"),
                    m.get("education"),
                    m.get("marital_status"),
                    1 if m.get("is_pregnant") else 0,
                    m.get("pregnancy_trimester"),
                    1 if m.get("is_lactating") else 0,
                    m.get("lactating_child_age_months"),
                    is_child_under_5,
                    1 if m.get("requires_immunization") else 0,
                    m.get("immunization_due"),
                    is_elderly,
                    1 if m.get("has_disability") else 0,
                    m.get("disability_type"),
                    m.get("chronic_conditions", "None"),
                    m.get("current_medications"),
                    m.get("recent_checkup_date"),
                    m.get("nutritional_status", "Normal"),
                    m.get("special_needs"),
                    now_iso,
                    now_iso
                )
            )

        # Record survey log (ensure survey_date is never None)
        survey_date = payload.get("survey_date") or date.today().strftime("%Y-%m-%d")
        survey_id = f"SRV-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            """
            INSERT INTO surveys (id, household_id, worker_id, survey_date, status, remarks, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                survey_id,
                household_id,
                user["id"],
                survey_date,
                survey_status,
                payload.get("remarks") or "Household survey recorded by ASHA worker.",
                now_iso,
                now_iso
            )
        )

    return get_household_details(household_id, user=user)

def update_household_and_survey(household_id: str, payload: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Updates an existing household, its survey status, and family members."""
    details = get_household_details(household_id, user=user)
    if not details:
        raise NotFoundError(f"Household with ID '{household_id}' not found.")

    check_worker_area_authorization(user, details["household"]["area_id"])
    now_iso = datetime.now().isoformat()

    with get_db() as conn:
        conn.execute(
            """
            UPDATE households
            SET head_of_family = ?, address = ?, contact_number = ?, pincode = ?, village = ?,
                house_type = ?, water_source = ?, toilet_available = ?, sanitation_facility = ?,
                survey_status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                payload.get("head_of_family", details["household"]["head_of_family"]),
                payload.get("address", details["household"]["address"]),
                payload.get("contact_number", details["household"]["contact_number"]),
                payload.get("pincode", details["household"]["pincode"]),
                payload.get("village", details["household"]["village"]),
                payload.get("house_type", details["household"]["house_type"]),
                payload.get("water_source", details["household"]["water_source"]),
                payload.get("toilet_available", details["household"]["toilet_available"]),
                payload.get("sanitation_facility", details["household"]["sanitation_facility"]),
                payload.get("survey_status", details["household"]["survey_status"]),
                now_iso,
                household_id
            )
        )

        # If updated members provided, replace them
        if "family_members" in payload:
            conn.execute("DELETE FROM family_members WHERE household_id = ?", (household_id,))
            for m in payload["family_members"]:
                mem_id = m.get("id") or f"MEM-{uuid.uuid4().hex[:8].upper()}"
                try:
                    age = int(m.get("age", 0))
                except (ValueError, TypeError):
                    age = 0
                is_elderly = 1 if (age >= 60 or m.get("is_elderly")) else 0
                is_child_under_5 = 1 if (age < 5 or m.get("is_child_under_5")) else 0

                conn.execute(
                    """
                    INSERT INTO family_members
                    (id, household_id, full_name, age, gender, dob, relationship, mobile, occupation, education,
                     marital_status, is_pregnant, pregnancy_trimester, is_lactating, lactating_child_age_months,
                     is_child_under_5, requires_immunization, immunization_due, is_elderly, has_disability,
                     disability_type, chronic_conditions, current_medications, recent_checkup_date,
                     nutritional_status, special_needs, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        mem_id, household_id, m.get("full_name", "Family Member"), age, m.get("gender", "Female"),
                        m.get("dob"), m.get("relationship", "Other"), m.get("mobile"), m.get("occupation"),
                        m.get("education"), m.get("marital_status"), 1 if m.get("is_pregnant") else 0,
                        m.get("pregnancy_trimester"), 1 if m.get("is_lactating") else 0,
                        m.get("lactating_child_age_months"), is_child_under_5, 1 if m.get("requires_immunization") else 0,
                        m.get("immunization_due"), is_elderly, 1 if m.get("has_disability") else 0,
                        m.get("disability_type"), m.get("chronic_conditions", "None"), m.get("current_medications"),
                        m.get("recent_checkup_date"), m.get("nutritional_status", "Normal"), m.get("special_needs"),
                        now_iso, now_iso
                    )
                )

        # Log survey update with audit notes
        survey_date = payload.get("survey_date") or date.today().strftime("%Y-%m-%d")
        survey_id = f"SRV-{uuid.uuid4().hex[:8].upper()}"
        worker_info = f"by {user.get('full_name', 'Worker')} ({user.get('role', 'worker')})"
        conn.execute(
            """
            INSERT INTO surveys (id, household_id, worker_id, survey_date, status, remarks, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                survey_id,
                household_id,
                user["id"],
                survey_date,
                payload.get("survey_status", details["household"]["survey_status"]),
                payload.get("remarks") or f"Household survey updated {worker_info}.",
                now_iso,
                now_iso
            )
        )

    return get_household_details(household_id, user=user)

def delete_household(household_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deletes a household and its associated family members and survey records.
    ASHA workers are restricted to their assigned area.
    """
    details = get_household_details(household_id, user=user)
    if not details:
        raise NotFoundError(f"Household with ID '{household_id}' not found.")

    check_worker_area_authorization(user, details["household"]["area_id"])
    hh_code = details["household"]["household_code"]
    head_name = details["household"]["head_of_family"]

    with get_db() as conn:
        conn.execute("DELETE FROM family_members WHERE household_id = ?", (household_id,))
        conn.execute("DELETE FROM surveys WHERE household_id = ?", (household_id,))
        conn.execute("DELETE FROM households WHERE id = ?", (household_id,))

    return {
        "status": "success",
        "message": f"Household record '{hh_code}' ({head_name}) deleted successfully.",
        "household_id": household_id,
        "household_code": hh_code,
        "deleted_by": user.get("id"),
        "deleted_at": datetime.now().isoformat()
    }

def add_family_member(household_id: str, member_data: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Adds a single new family member to an existing household."""
    details = get_household_details(household_id, user=user)
    if not details:
        raise NotFoundError(f"Household with ID '{household_id}' not found.")

    check_worker_area_authorization(user, details["household"]["area_id"])
    now_iso = datetime.now().isoformat()
    mem_id = f"MEM-{uuid.uuid4().hex[:8].upper()}"

    try:
        age = int(member_data.get("age", 0))
    except (ValueError, TypeError):
        age = 0
    is_elderly = 1 if (age >= 60 or member_data.get("is_elderly")) else 0
    is_child_under_5 = 1 if (age < 5 or member_data.get("is_child_under_5")) else 0
    name = str(member_data.get("full_name") or "").strip() or "Family Member"

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO family_members
            (id, household_id, full_name, age, gender, dob, relationship, mobile, occupation, education,
             marital_status, is_pregnant, pregnancy_trimester, is_lactating, lactating_child_age_months,
             is_child_under_5, requires_immunization, immunization_due, is_elderly, has_disability,
             disability_type, chronic_conditions, current_medications, recent_checkup_date,
             nutritional_status, special_needs, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mem_id, household_id, name, age, member_data.get("gender", "Female"),
                member_data.get("dob"), member_data.get("relationship", "Other"), member_data.get("mobile"),
                member_data.get("occupation"), member_data.get("education"), member_data.get("marital_status"),
                1 if member_data.get("is_pregnant") else 0, member_data.get("pregnancy_trimester"),
                1 if member_data.get("is_lactating") else 0, member_data.get("lactating_child_age_months"),
                is_child_under_5, 1 if member_data.get("requires_immunization") else 0,
                member_data.get("immunization_due"), is_elderly, 1 if member_data.get("has_disability") else 0,
                member_data.get("disability_type"), member_data.get("chronic_conditions", "None"),
                member_data.get("current_medications"), member_data.get("recent_checkup_date"),
                member_data.get("nutritional_status", "Normal"), member_data.get("special_needs"),
                now_iso, now_iso
            )
        )
        conn.execute("UPDATE households SET updated_at = ? WHERE id = ?", (now_iso, household_id))

    return get_household_details(household_id, user=user)

def update_family_member(household_id: str, member_id: str, member_data: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Updates an individual family member's details."""
    details = get_household_details(household_id, user=user)
    if not details:
        raise NotFoundError(f"Household with ID '{household_id}' not found.")

    check_worker_area_authorization(user, details["household"]["area_id"])
    now_iso = datetime.now().isoformat()

    with get_db() as conn:
        existing = conn.execute("SELECT * FROM family_members WHERE id = ? AND household_id = ?", (member_id, household_id)).fetchone()
        if not existing:
            raise NotFoundError(f"Family member with ID '{member_id}' not found in household '{household_id}'.")

        try:
            age = int(member_data.get("age", existing["age"]))
        except (ValueError, TypeError):
            age = existing["age"]
        is_elderly = 1 if (age >= 60 or member_data.get("is_elderly")) else 0
        is_child_under_5 = 1 if (age < 5 or member_data.get("is_child_under_5")) else 0

        conn.execute(
            """
            UPDATE family_members
            SET full_name = ?, age = ?, gender = ?, dob = ?, relationship = ?, mobile = ?,
                occupation = ?, education = ?, marital_status = ?, is_pregnant = ?,
                pregnancy_trimester = ?, is_lactating = ?, lactating_child_age_months = ?,
                is_child_under_5 = ?, requires_immunization = ?, immunization_due = ?,
                is_elderly = ?, has_disability = ?, disability_type = ?, chronic_conditions = ?,
                current_medications = ?, recent_checkup_date = ?, nutritional_status = ?,
                special_needs = ?, updated_at = ?
            WHERE id = ? AND household_id = ?
            """,
            (
                member_data.get("full_name", existing["full_name"]),
                age,
                member_data.get("gender", existing["gender"]),
                member_data.get("dob", existing["dob"]),
                member_data.get("relationship", existing["relationship"]),
                member_data.get("mobile", existing["mobile"]),
                member_data.get("occupation", existing["occupation"]),
                member_data.get("education", existing["education"]),
                member_data.get("marital_status", existing["marital_status"]),
                1 if member_data.get("is_pregnant", existing["is_pregnant"]) else 0,
                member_data.get("pregnancy_trimester", existing["pregnancy_trimester"]),
                1 if member_data.get("is_lactating", existing["is_lactating"]) else 0,
                member_data.get("lactating_child_age_months", existing["lactating_child_age_months"]),
                is_child_under_5,
                1 if member_data.get("requires_immunization", existing["requires_immunization"]) else 0,
                member_data.get("immunization_due", existing["immunization_due"]),
                is_elderly,
                1 if member_data.get("has_disability", existing["has_disability"]) else 0,
                member_data.get("disability_type", existing["disability_type"]),
                member_data.get("chronic_conditions", existing["chronic_conditions"]),
                member_data.get("current_medications", existing["current_medications"]),
                member_data.get("recent_checkup_date", existing["recent_checkup_date"]),
                member_data.get("nutritional_status", existing["nutritional_status"]),
                member_data.get("special_needs", existing["special_needs"]),
                now_iso,
                member_id,
                household_id
            )
        )
        conn.execute("UPDATE households SET updated_at = ? WHERE id = ?", (now_iso, household_id))

    return get_household_details(household_id, user=user)

def delete_family_member(household_id: str, member_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """Deletes an individual family member from a household."""
    details = get_household_details(household_id, user=user)
    if not details:
        raise NotFoundError(f"Household with ID '{household_id}' not found.")

    check_worker_area_authorization(user, details["household"]["area_id"])

    if details["member_count"] <= 1:
        raise ValidationError("Cannot delete the only remaining family member. A household must have at least one member.")

    with get_db() as conn:
        existing = conn.execute("SELECT full_name FROM family_members WHERE id = ? AND household_id = ?", (member_id, household_id)).fetchone()
        if not existing:
            raise NotFoundError(f"Family member with ID '{member_id}' not found in household '{household_id}'.")

        mem_name = existing["full_name"]
        conn.execute("DELETE FROM family_members WHERE id = ? AND household_id = ?", (member_id, household_id))
        now_iso = datetime.now().isoformat()
        conn.execute("UPDATE households SET updated_at = ? WHERE id = ?", (now_iso, household_id))

    return {
        "status": "success",
        "message": f"Family member '{mem_name}' deleted successfully.",
        "household_id": household_id,
        "member_id": member_id,
        "updated_details": get_household_details(household_id, user=user)
    }


# ============================================================================
# COMPREHENSIVE DASHBOARD ANALYTICS
# ============================================================================

def get_survey_analytics(
    user: Optional[Dict[str, Any]] = None,
    pincode: Optional[str] = None,
    village: Optional[str] = None,
    worker_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes dashboard statistics and visual analytics:
    - Total households registered
    - Total population surveyed
    - Total male, female, other residents
    - Total children under 5
    - Total children requiring immunization
    - Total pregnant women
    - Total lactating mothers
    - Total elderly residents (60+)
    - Total people with disabilities
    - Households pending survey vs completed
    - Water source, sanitation, and housing breakdowns
    """
    with get_db() as conn:
        # Build base filter
        where_clauses = ["1=1"]
        params = []

        if user and user.get("role") == "asha_worker":
            assigned_area = user.get("assigned_area_id")
            if assigned_area:
                where_clauses.append("h.area_id = ?")
                params.append(assigned_area)

        if pincode:
            where_clauses.append("h.pincode = ?")
            params.append(pincode.strip())
        if village:
            where_clauses.append("h.village LIKE ?")
            params.append(f"%{village.strip()}%")
        if worker_id:
            where_clauses.append("h.created_by_worker_id = ?")
            params.append(worker_id.strip())

        where_str = " AND ".join(where_clauses)

        total_households = conn.execute(f"SELECT COUNT(*) FROM households h WHERE {where_str}", params).fetchone()[0]
        completed_surveys = conn.execute(f"SELECT COUNT(*) FROM households h WHERE {where_str} AND h.survey_status = 'completed'", params).fetchone()[0]
        pending_surveys = conn.execute(f"SELECT COUNT(*) FROM households h WHERE {where_str} AND h.survey_status IN ('pending', 'draft')", params).fetchone()[0]

        # Population and health metrics
        member_query = f"""
            SELECT 
                COUNT(*) as total_pop,
                SUM(CASE WHEN m.gender = 'Male' THEN 1 ELSE 0 END) as male_count,
                SUM(CASE WHEN m.gender = 'Female' THEN 1 ELSE 0 END) as female_count,
                SUM(CASE WHEN m.gender NOT IN ('Male', 'Female') THEN 1 ELSE 0 END) as other_count,
                SUM(CASE WHEN m.is_child_under_5 = 1 OR m.age < 5 THEN 1 ELSE 0 END) as children_under_5,
                SUM(CASE WHEN m.requires_immunization = 1 THEN 1 ELSE 0 END) as immunization_due,
                SUM(CASE WHEN m.is_pregnant = 1 THEN 1 ELSE 0 END) as pregnant_women,
                SUM(CASE WHEN m.is_lactating = 1 THEN 1 ELSE 0 END) as lactating_mothers,
                SUM(CASE WHEN m.is_elderly = 1 OR m.age >= 60 THEN 1 ELSE 0 END) as elderly_count,
                SUM(CASE WHEN m.has_disability = 1 THEN 1 ELSE 0 END) as disability_count
            FROM family_members m
            JOIN households h ON m.household_id = h.id
            WHERE {where_str}
        """
        pop_row = conn.execute(member_query, params).fetchone()

        # Infrastructure breakdowns
        water_rows = conn.execute(
            f"SELECT h.water_source, COUNT(*) FROM households h WHERE {where_str} GROUP BY h.water_source",
            params
        ).fetchall()
        toilet_rows = conn.execute(
            f"SELECT h.toilet_available, COUNT(*) FROM households h WHERE {where_str} GROUP BY h.toilet_available",
            params
        ).fetchall()
        house_type_rows = conn.execute(
            f"SELECT h.house_type, COUNT(*) FROM households h WHERE {where_str} GROUP BY h.house_type",
            params
        ).fetchall()
        sanitation_rows = conn.execute(
            f"SELECT h.sanitation_facility, COUNT(*) FROM households h WHERE {where_str} GROUP BY h.sanitation_facility",
            params
        ).fetchall()

        # Distinct villages & pincodes for filter dropdowns
        all_pincodes = [r[0] for r in conn.execute("SELECT DISTINCT pincode FROM households ORDER BY pincode").fetchall()]
        all_villages = [r[0] for r in conn.execute("SELECT DISTINCT village FROM households ORDER BY village").fetchall()]

        return {
            "total_households_registered": total_households,
            "total_population_surveyed": pop_row["total_pop"] or 0,
            "total_male_residents": pop_row["male_count"] or 0,
            "total_female_residents": pop_row["female_count"] or 0,
            "total_other_residents": pop_row["other_count"] or 0,
            "total_children_under_5": pop_row["children_under_5"] or 0,
            "total_children_immunization_due": pop_row["immunization_due"] or 0,
            "total_pregnant_women": pop_row["pregnant_women"] or 0,
            "total_lactating_mothers": pop_row["lactating_mothers"] or 0,
            "total_elderly_residents": pop_row["elderly_count"] or 0,
            "total_disability_cases": pop_row["disability_count"] or 0,
            "total_completed_surveys": completed_surveys,
            "total_pending_surveys": pending_surveys,
            "infrastructure": {
                "water_sources": [{"label": r[0], "count": r[1]} for r in water_rows],
                "toilet_availability": [{"label": r[0], "count": r[1]} for r in toilet_rows],
                "house_types": [{"label": r[0], "count": r[1]} for r in house_type_rows],
                "sanitation_facilities": [{"label": r[0], "count": r[1]} for r in sanitation_rows]
            },
            "available_filters": {
                "pincodes": all_pincodes,
                "villages": all_villages
            },
            "data_label": "SYNTHETIC DEMO DATA - FOR HACKATHON EVALUATION ONLY",
            "generated_at": datetime.now().isoformat()
        }


# ============================================================================
# PRESERVED PHASE 3 FUNCTIONS (Visits, Beneficiaries, Follow-ups, Reports)
# ============================================================================

def compute_submission_hash(beneficiary_id: str, visit_type: str, visit_date: str, weight: Optional[str], vaccinations: List[str]) -> str:
    """Computes a deterministic hash to prevent duplicate submissions."""
    normalized = f"{beneficiary_id.strip()}|{visit_type.strip()}|{visit_date.strip()}|{weight or ''}|{','.join(sorted(vaccinations))}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def save_confirmed_visit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Saves a confirmed visit record received from Phase 2 into persistent SQLite database."""
    is_valid, err_msg, sanitized = validate_confirmed_visit_payload(payload)
    if not is_valid:
        raise ValidationError(err_msg)

    beneficiary_id = sanitized["beneficiary_id"]
    beneficiary_name = sanitized.get("beneficiary_name")
    age = sanitized.get("age")
    visit_type = sanitized["visit_type"]
    weight = sanitized["weight"]
    blood_pressure = sanitized.get("blood_pressure")
    gestational_age = sanitized.get("gestational_age")
    vaccinations_due = sanitized["vaccinations_due"]
    symptoms_reported = sanitized.get("symptoms_reported", [])
    negated_symptoms = sanitized.get("negated_symptoms", [])
    next_visit_date = sanitized["next_visit_date"]
    danger_signs = sanitized["danger_signs"]
    referral_required = 1 if (sanitized["referral_required"] or len(danger_signs) > 0) else 0
    visit_date = sanitized["visit_date"]
    worker_id = sanitized.get("worker_id")
    raw_transcript = sanitized.get("raw_transcript")
    now_iso = datetime.now().isoformat()

    sub_hash = compute_submission_hash(beneficiary_id, visit_type, visit_date, weight, vaccinations_due)

    with get_db() as conn:
        existing = conn.execute(
            "SELECT visit_id, created_at FROM visits WHERE submission_hash = ? OR (beneficiary_id = ? AND visit_type = ? AND visit_date = ?)",
            (sub_hash, beneficiary_id, visit_type, visit_date)
        ).fetchone()

        if existing:
            raise DuplicateVisitError(
                f"Duplicate submission detected: A confirmed record for beneficiary '{beneficiary_id}' "
                f"with visit type '{visit_type}' on date '{visit_date}' already exists (ID: {existing['visit_id']})."
            )

        # Upsert Beneficiary record
        ben_row = conn.execute("SELECT beneficiary_id, full_name, age_years FROM beneficiaries WHERE beneficiary_id = ?", (beneficiary_id,)).fetchone()
        display_name = beneficiary_name or f"Beneficiary {beneficiary_id}"
        if not ben_row:
            conn.execute(
                """
                INSERT INTO beneficiaries 
                (beneficiary_id, full_name, age_years, gender, category, village_ward, contact_number, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (beneficiary_id, display_name, age or 25, "Female", "Field Registered Beneficiary", "Assigned Ward", "Available via ASHA", "Registered via ASHA Sahayak Phase 2 voice flow.", now_iso, now_iso)
            )
        elif beneficiary_name:
            conn.execute(
                "UPDATE beneficiaries SET full_name = ?, age_years = COALESCE(?, age_years), updated_at = ? WHERE beneficiary_id = ?",
                (beneficiary_name, age, now_iso, beneficiary_id)
            )

        visit_id = f"VIS-{uuid.uuid4().hex[:8].upper()}"
        referral_facility = "Primary Health Centre (PHC)" if referral_required else "Not Required"
        referral_status = "Pending PHC Referral" if referral_required else "Not Required"

        conn.execute(
            """
            INSERT INTO visits 
            (visit_id, beneficiary_id, beneficiary_name, age, visit_type, weight, blood_pressure,
             gestational_age, vaccinations_due, symptoms_reported, negated_symptoms, next_visit_date, 
             danger_signs, referral_required, referral_facility, referral_status, 
             confirmation_status, raw_transcript, worker_id, submission_hash, visit_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (visit_id, beneficiary_id, display_name, age, visit_type, weight, blood_pressure,
             gestational_age, json.dumps(vaccinations_due), json.dumps(symptoms_reported),
             json.dumps(negated_symptoms), next_visit_date, json.dumps(danger_signs),
             referral_required, referral_facility, referral_status, "confirmed",
             raw_transcript, worker_id, sub_hash, visit_date, now_iso)
        )

        created_followup_id = None
        if next_visit_date:
            created_followup_id = f"FOL-{uuid.uuid4().hex[:8].upper()}"
            reason_parts = [f"Scheduled follow-up for {visit_type}"]
            if vaccinations_due:
                reason_parts.append(f"Vaccinations check: {', '.join(vaccinations_due)}")
            if referral_required:
                reason_parts.append("Verify PHC Referral attendance")

            conn.execute(
                """
                INSERT INTO follow_ups 
                (followup_id, visit_id, beneficiary_id, scheduled_date, status, reason, 
                 worker_notes, updated_by, completed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (created_followup_id, visit_id, beneficiary_id, next_visit_date, "upcoming", " | ".join(reason_parts),
                 "Automatically scheduled from worker-confirmed visit report.", "ASHA-System", None, now_iso, now_iso)
            )

    return {
        "status": "success",
        "message": "Visit record successfully saved into database.",
        "visit_id": visit_id,
        "beneficiary_id": beneficiary_id,
        "beneficiary_name": display_name,
        "age": age,
        "visit_type": visit_type,
        "weight": weight,
        "blood_pressure": blood_pressure,
        "gestational_age": gestational_age,
        "vaccinations_due": vaccinations_due,
        "symptoms_reported": symptoms_reported,
        "negated_symptoms": negated_symptoms,
        "next_visit_date": next_visit_date,
        "danger_signs": danger_signs,
        "referral_required": bool(referral_required),
        "referral_status": referral_status,
        "followup_created": created_followup_id is not None,
        "followup_id": created_followup_id,
        "created_at": now_iso
    }

def get_visits(beneficiary_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    with get_db() as conn:
        query = """
            SELECT v.*, COALESCE(v.beneficiary_name, b.full_name) as beneficiary_name, b.village_ward, b.category as beneficiary_category
            FROM visits v
            LEFT JOIN beneficiaries b ON v.beneficiary_id = b.beneficiary_id
        """
        params = []
        if beneficiary_id:
            query += " WHERE v.beneficiary_id = ?"
            params.append(beneficiary_id.strip().upper())
        query += " ORDER BY v.visit_date DESC, v.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["id"] = d.get("visit_id")
            d["vaccinations_due"] = json.loads(d["vaccinations_due"]) if d.get("vaccinations_due") else []
            d["danger_signs"] = json.loads(d["danger_signs"]) if d.get("danger_signs") else []
            d["symptoms_reported"] = json.loads(d["symptoms_reported"]) if d.get("symptoms_reported") else []
            d["negated_symptoms"] = json.loads(d["negated_symptoms"]) if d.get("negated_symptoms") else []
            d["referral_required"] = bool(d["referral_required"])
            result.append(d)
        return result

def get_beneficiaries(search: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    with get_db() as conn:
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = """
                SELECT b.*,
                    (SELECT COUNT(*) FROM visits WHERE beneficiary_id = b.beneficiary_id) as total_visits,
                    (SELECT COUNT(*) FROM follow_ups WHERE beneficiary_id = b.beneficiary_id AND status IN ('upcoming', 'overdue')) as active_followups
                FROM beneficiaries b
                WHERE b.beneficiary_id LIKE ? OR b.full_name LIKE ? OR b.village_ward LIKE ?
                ORDER BY b.beneficiary_id ASC LIMIT ?
            """
            rows = conn.execute(query, (term, term, term, limit)).fetchall()
        else:
            query = """
                SELECT b.*,
                    (SELECT COUNT(*) FROM visits WHERE beneficiary_id = b.beneficiary_id) as total_visits,
                    (SELECT COUNT(*) FROM follow_ups WHERE beneficiary_id = b.beneficiary_id AND status IN ('upcoming', 'overdue')) as active_followups
                FROM beneficiaries b
                ORDER BY b.beneficiary_id ASC LIMIT ?
            """
            rows = conn.execute(query, (limit,)).fetchall()

        return [dict(r) for r in rows]

def get_beneficiary_details(beneficiary_id: str) -> Optional[Dict[str, Any]]:
    ben_id = beneficiary_id.strip().upper()
    with get_db() as conn:
        ben_row = conn.execute("SELECT * FROM beneficiaries WHERE beneficiary_id = ?", (ben_id,)).fetchone()
        if not ben_row:
            return None

        beneficiary = dict(ben_row)
        visits = get_visits(beneficiary_id=ben_id)

        fol_rows = conn.execute(
            "SELECT * FROM follow_ups WHERE beneficiary_id = ? ORDER BY scheduled_date ASC",
            (ben_id,)
        ).fetchall()
        
        today_str = date.today().strftime("%Y-%m-%d")
        follow_ups = []
        for fr in fol_rows:
            f = dict(fr)
            if f["status"] == "upcoming" and f["scheduled_date"] < today_str:
                f["status"] = "overdue"
            follow_ups.append(f)

        all_vaccines = set()
        for v in visits:
            for vac in v.get("vaccinations_due", []):
                all_vaccines.add(vac)

        return {
            "beneficiary": beneficiary,
            "visits": visits,
            "follow_ups": follow_ups,
            "vaccinations_due": sorted(list(all_vaccines)),
            "total_visits": len(visits),
            "pending_followups_count": sum(1 for f in follow_ups if f["status"] in ("upcoming", "overdue"))
        }

def get_followups(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    today_str = date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute(
            "UPDATE follow_ups SET status = 'overdue' WHERE status = 'upcoming' AND scheduled_date < ?",
            (today_str,)
        )

        query = """
            SELECT f.*, b.full_name as beneficiary_name, b.village_ward, b.contact_number
            FROM follow_ups f
            LEFT JOIN beneficiaries b ON f.beneficiary_id = b.beneficiary_id
        """
        params = []
        if status_filter:
            norm_status = status_filter.strip().lower()
            if norm_status in ("upcoming", "overdue", "completed", "cancelled"):
                query += " WHERE f.status = ?"
                params.append(norm_status)
            elif norm_status == "pending":
                query += " WHERE f.status IN ('upcoming', 'overdue')"

        query += " ORDER BY f.scheduled_date ASC, f.created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def update_followup_status(followup_id: str, new_status: str, worker_notes: Optional[str] = None, worker_id: str = "ASHA-Worker") -> Dict[str, Any]:
    valid_statuses = ("upcoming", "overdue", "completed", "cancelled")
    clean_status = new_status.strip().lower()
    if clean_status not in valid_statuses:
        raise ValidationError(f"Invalid status '{new_status}'. Allowed: {', '.join(valid_statuses)}")

    now_iso = datetime.now().isoformat()
    completed_at = now_iso if clean_status == "completed" else None

    with get_db() as conn:
        row = conn.execute("SELECT * FROM follow_ups WHERE followup_id = ?", (followup_id,)).fetchone()
        if not row:
            raise NotFoundError(f"Follow-up with ID '{followup_id}' not found.")

        updated_notes = worker_notes.strip() if worker_notes else row["worker_notes"]

        conn.execute(
            """
            UPDATE follow_ups 
            SET status = ?, worker_notes = ?, updated_by = ?, completed_at = ?, updated_at = ?
            WHERE followup_id = ?
            """,
            (clean_status, updated_notes, worker_id, completed_at, now_iso, followup_id)
        )

        updated_row = conn.execute("SELECT * FROM follow_ups WHERE followup_id = ?", (followup_id,)).fetchone()
        return dict(updated_row)

def get_dashboard_reports() -> Dict[str, Any]:
    today_str = date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute(
            "UPDATE follow_ups SET status = 'overdue' WHERE status = 'upcoming' AND scheduled_date < ?",
            (today_str,)
        )

        total_beneficiaries = conn.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0]
        total_visits = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        upcoming_followups = conn.execute("SELECT COUNT(*) FROM follow_ups WHERE status = 'upcoming'").fetchone()[0]
        overdue_followups = conn.execute("SELECT COUNT(*) FROM follow_ups WHERE status = 'overdue'").fetchone()[0]
        completed_followups = conn.execute("SELECT COUNT(*) FROM follow_ups WHERE status = 'completed'").fetchone()[0]
        referral_cases = conn.execute("SELECT COUNT(*) FROM visits WHERE referral_required = 1").fetchone()[0]

        visit_rows = conn.execute("SELECT vaccinations_due FROM visits").fetchall()
        vaccine_counts: Dict[str, int] = {}
        for vr in visit_rows:
            if vr[0]:
                try:
                    vacs = json.loads(vr[0])
                    for v in vacs:
                        vac_name = v.strip().upper()
                        vaccine_counts[vac_name] = vaccine_counts.get(vac_name, 0) + 1
                except Exception:
                    pass

        danger_rows = conn.execute("SELECT danger_signs FROM visits WHERE referral_required = 1").fetchall()
        danger_counts: Dict[str, int] = {}
        for dr in danger_rows:
            if dr[0]:
                try:
                    ds = json.loads(dr[0])
                    for d in ds:
                        d_name = d.strip()
                        danger_counts[d_name] = danger_counts.get(d_name, 0) + 1
                except Exception:
                    pass

        referral_alerts = conn.execute(
            """
            SELECT v.visit_id, v.beneficiary_id, v.visit_type, v.visit_date, v.danger_signs,
                   v.referral_facility, v.referral_status, b.full_name as beneficiary_name, b.village_ward
            FROM visits v
            LEFT JOIN beneficiaries b ON v.beneficiary_id = b.beneficiary_id
            WHERE v.referral_required = 1
            ORDER BY v.visit_date DESC, v.created_at DESC LIMIT 5
            """
        ).fetchall()

        parsed_alerts = []
        for ra in referral_alerts:
            d = dict(ra)
            d["danger_signs"] = json.loads(d["danger_signs"]) if d["danger_signs"] else []
            parsed_alerts.append(d)

    return {
        "data_label": "SYNTHETIC DEMO DATA - FOR HACKATHON EVALUATION ONLY",
        "total_beneficiaries": total_beneficiaries,
        "total_completed_visits": total_visits,
        "upcoming_followups": upcoming_followups,
        "overdue_followups": overdue_followups,
        "pending_followups": upcoming_followups + overdue_followups,
        "completed_followups": completed_followups,
        "referral_cases": referral_cases,
        "vaccinations_due_summary": [
            {"vaccine": k, "count": v} for k, v in sorted(vaccine_counts.items(), key=lambda x: x[1], reverse=True)
        ],
        "danger_signs_summary": [
            {"sign": k, "count": v} for k, v in sorted(danger_counts.items(), key=lambda x: x[1], reverse=True)
        ],
        "recent_referral_alerts": parsed_alerts,
        "generated_at": datetime.now().isoformat()
    }


# ============================================================================
# LOCATION-BASED ASHA WORKER FINDER, DASHBOARD & MANAGEMENT CRUD
# ============================================================================

def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    import math
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999.0
    r_earth = 6371.0 # Radius of Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r_earth * c, 2)

def find_asha_workers(
    query: Optional[str] = None,
    name: Optional[str] = None,
    worker_id: Optional[str] = None,
    phc_name: Optional[str] = None,
    pincode: Optional[str] = None,
    village: Optional[str] = None,
    locality: Optional[str] = None,
    taluk: Optional[str] = None,
    district: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    max_distance_km: float = 35.0
) -> List[Dict[str, Any]]:
    """
    Finds officially verified and active ASHA workers matching location/identity criteria.
    Supports search by Name, Worker ID, Village, PIN code, PHC, Taluk, District, or GPS coordinates.
    Strictly sanitizes output: excludes password hashes or private patient data.
    """
    with get_db() as conn:
        sql = """
            SELECT 
                u.id as worker_id,
                u.full_name as worker_name,
                COALESCE(u.badge_id, u.id) as badge_id,
                COALESCE(u.phc_name, a.phc_name, 'Primary Health Centre') as phc_name,
                COALESCE(u.work_contact, u.mobile, 'Available via PHC') as work_contact,
                u.mobile,
                u.is_verified,
                u.is_active,
                u.updated_at,
                u.created_at,
                a.id as area_id,
                a.village,
                a.area_name,
                a.pincode,
                a.taluk,
                a.district,
                a.state,
                a.latitude,
                a.longitude
            FROM users u
            LEFT JOIN areas a ON u.assigned_area_id = a.id
            WHERE u.role = 'asha_worker'
              AND (u.is_active = 1 OR u.is_active IS NULL)
              AND (u.is_verified = 1 OR u.is_verified IS NULL)
        """
        params = []
        clauses = []

        order_clauses = []
        if name and name.strip():
            clauses.append("LOWER(u.full_name) LIKE ?")
            params.append(f"%{name.strip().lower()}%")

        if worker_id and worker_id.strip():
            w_clean = worker_id.strip().lower()
            clauses.append("(LOWER(u.id) = ? OR LOWER(COALESCE(u.badge_id, '')) = ? OR LOWER(u.id) LIKE ? OR LOWER(COALESCE(u.badge_id, '')) LIKE ?)")
            params.extend([w_clean, w_clean, f"%{w_clean}%", f"%{w_clean}%"])
            order_clauses.append(f"CASE WHEN LOWER(u.id) = '{w_clean}' THEN 0 ELSE 1 END")

        if phc_name and phc_name.strip():
            clauses.append("(LOWER(COALESCE(u.phc_name, '')) LIKE ? OR LOWER(COALESCE(a.phc_name, '')) LIKE ?)")
            params.extend([f"%{phc_name.strip().lower()}%", f"%{phc_name.strip().lower()}%"])

        if pincode and pincode.strip():
            clauses.append("a.pincode LIKE ?")
            params.append(f"%{pincode.strip()}%")

        if village and village.strip():
            clauses.append("LOWER(a.village) LIKE ?")
            params.append(f"%{village.strip().lower()}%")

        if locality and locality.strip():
            clauses.append("LOWER(a.area_name) LIKE ?")
            params.append(f"%{locality.strip().lower()}%")

        if taluk and taluk.strip():
            clauses.append("LOWER(a.taluk) LIKE ?")
            params.append(f"%{taluk.strip().lower()}%")

        if district and district.strip():
            clauses.append("LOWER(a.district) LIKE ?")
            params.append(f"%{district.strip().lower()}%")

        if query and query.strip():
            q_clean = f"%{query.strip().lower()}%"
            clauses.append(
                "(LOWER(COALESCE(a.village, '')) LIKE ? OR LOWER(COALESCE(a.area_name, '')) LIKE ? OR COALESCE(a.pincode, '') LIKE ? OR "
                "LOWER(COALESCE(a.taluk, '')) LIKE ? OR LOWER(COALESCE(a.district, '')) LIKE ? OR LOWER(u.full_name) LIKE ? OR "
                "LOWER(COALESCE(u.badge_id, '')) LIKE ? OR LOWER(u.id) LIKE ? OR LOWER(COALESCE(u.phc_name, '')) LIKE ? OR "
                "LOWER(COALESCE(a.phc_name, '')) LIKE ?)"
            )
            params.extend([q_clean] * 10)

        if clauses:
            sql += " AND (" + " AND ".join(clauses) + ")"

        order_clauses.extend(["a.district", "a.taluk", "a.village", "u.full_name"])
        sql += " ORDER BY " + ", ".join(order_clauses)
        rows = conn.execute(sql, params).fetchall()

        results = []
        for r in rows:
            dist = None
            if latitude is not None and longitude is not None and r["latitude"] is not None and r["longitude"] is not None:
                dist = _haversine_distance(latitude, longitude, r["latitude"], r["longitude"])
                if dist > max_distance_km and (pincode or village or locality or taluk or district or query or name or worker_id):
                    pass
                elif dist > max_distance_km and not (pincode or village or locality or taluk or district or query or name or worker_id):
                    continue

            service_area = f"{r['village']} - {r['area_name']} ({r['taluk']} Taluk, {r['district']})"
            results.append({
                "worker_id": r["worker_id"],
                "badge_id": r["badge_id"],
                "full_name": r["worker_name"],
                "name": r["worker_name"],
                "mobile": r["mobile"] or r["work_contact"],
                "village": r["village"] or "Assigned Sector",
                "area_name": r["area_name"] or "Designated Ward",
                "sector": r["area_name"] or "Designated Ward",
                "pincode": r["pincode"] or "N/A",
                "taluk": r["taluk"] or "N/A",
                "district": r["district"] or "N/A",
                "state": r["state"] or "Karnataka",
                "phc_name": r["phc_name"],
                "assigned_phc": r["phc_name"],
                "designated_service_area": service_area,
                "work_contact": r["work_contact"],
                "account_status": "Active" if (r["is_active"] is None or r["is_active"] == 1) else "Inactive",
                "is_verified": bool(r["is_verified"] if r["is_verified"] is not None else True),
                "verification_status": "Verified & Registered with Health Department" if (r["is_verified"] is None or r["is_verified"] == 1) else "Pending Department Approval",
                "last_updated": r["updated_at"] or r["created_at"],
                "distance_km": dist
            })

        if latitude is not None and longitude is not None:
            results.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else 999999))

        return results

def get_worker_dashboard_summary(worker_id: str) -> Dict[str, Any]:
    """
    Returns personalized dashboard metrics, area details, today's schedule,
    and high-risk beneficiary alerts for an ASHA worker.
    """
    with get_db() as conn:
        worker = conn.execute(
            """
            SELECT u.id, u.username, u.full_name, u.role, u.mobile, u.badge_id,
                   u.phc_name, u.work_contact, u.assigned_area_id,
                   a.village, a.area_name, a.pincode, a.taluk, a.district
            FROM users u
            LEFT JOIN areas a ON u.assigned_area_id = a.id
            WHERE u.id = ?
            """,
            (worker_id,)
        ).fetchone()

        if not worker:
            raise NotFoundError(f"Worker with ID '{worker_id}' not found.")

        area_id = worker["assigned_area_id"]
        today_str = date.today().isoformat()

        # Households in worker's area
        hh_stats = conn.execute(
            """
            SELECT 
                COUNT(*) as total_households,
                SUM(CASE WHEN survey_status = 'completed' THEN 1 ELSE 0 END) as surveys_completed,
                SUM(CASE WHEN survey_status != 'completed' THEN 1 ELSE 0 END) as surveys_pending
            FROM households
            WHERE area_id = ? OR created_by_worker_id = ?
            """,
            (area_id, worker_id)
        ).fetchone()

        total_households = hh_stats["total_households"] or 0
        surveys_completed = hh_stats["surveys_completed"] or 0
        surveys_pending = hh_stats["surveys_pending"] or 0
        completion_rate = round((surveys_completed / total_households * 100), 1) if total_households > 0 else 0.0

        # Total population
        pop_count = conn.execute(
            """
            SELECT COUNT(*) 
            FROM family_members m
            JOIN households h ON m.household_id = h.id
            WHERE h.area_id = ? OR h.created_by_worker_id = ?
            """,
            (area_id, worker_id)
        ).fetchone()[0]

        # High-risk members in worker's area
        high_risk_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM family_members m
            JOIN households h ON m.household_id = h.id
            WHERE (h.area_id = ? OR h.created_by_worker_id = ?)
              AND (m.is_pregnant = 1 OR m.is_child_under_5 = 1 OR m.has_disability = 1 OR (m.is_elderly = 1 AND m.chronic_conditions IS NOT NULL))
            """,
            (area_id, worker_id)
        ).fetchone()[0]

        # Today's visits
        today_visits_count = conn.execute(
            "SELECT COUNT(*) FROM visits WHERE visit_date = ?",
            (today_str,)
        ).fetchone()[0]

        today_visits_list = conn.execute(
            """
            SELECT v.visit_id, v.beneficiary_id, v.visit_type, v.visit_date,
                   v.confirmation_status, v.danger_signs, v.referral_required,
                   b.full_name as beneficiary_name, b.category, b.village_ward
            FROM visits v
            LEFT JOIN beneficiaries b ON v.beneficiary_id = b.beneficiary_id
            ORDER BY v.visit_date DESC, v.created_at DESC
            LIMIT 5
            """
        ).fetchall()

        # Pending and upcoming followups
        pending_followups_count = conn.execute(
            "SELECT COUNT(*) FROM follow_ups WHERE status IN ('upcoming', 'overdue')"
        ).fetchone()[0]

        upcoming_followups_list = conn.execute(
            """
            SELECT f.followup_id, f.visit_id, f.beneficiary_id, f.scheduled_date, f.status, f.reason,
                   b.full_name as beneficiary_name, b.village_ward
            FROM follow_ups f
            LEFT JOIN beneficiaries b ON f.beneficiary_id = b.beneficiary_id
            WHERE f.status IN ('upcoming', 'overdue')
            ORDER BY f.scheduled_date ASC
            LIMIT 5
            """
        ).fetchall()

        parsed_visits = []
        for tv in today_visits_list:
            v_dict = dict(tv)
            v_dict["danger_signs"] = json.loads(v_dict["danger_signs"]) if v_dict["danger_signs"] else []
            parsed_visits.append(v_dict)

        parsed_followups = [dict(f) for f in upcoming_followups_list]

        quick_navigation = [
            {"id": "nav-survey", "label": "Household Registration", "label_kn": "ಮನೆ ಸಮೀಕ್ಷೆ ನೋಂದಣಿ", "path": "#survey-form", "icon": "📝"},
            {"id": "nav-directory", "label": "Household Directory", "label_kn": "ಮನೆಗಳ ಡೈರೆಕ್ಟರಿ (ತಿದ್ದುಪಡಿ/ಅಳಿಸಿ)", "path": "#households", "icon": "🏘️"},
            {"id": "nav-visits", "label": "Visit Records & Clinical Register", "label_kn": "ಭೇಟಿ ದಾಖಲೆಗಳು ಮತ್ತು ರಿಜಿಸ್ಟರ್", "path": "#visits", "icon": "🩺"},
            {"id": "nav-followups", "label": "Follow-up Tracking", "label_kn": "ಫಾಲೋ-ಅಪ್ ಟ್ರ್ಯಾಕಿಂಗ್", "path": "#followups", "icon": "📅"},
            {"id": "nav-highrisk", "label": "High-Risk Beneficiaries & Alerts", "label_kn": "ಹೆಚ್ಚಿನ ಅಪಾಯದ ಫಲಾನುಭವಿಗಳು", "path": "#highrisk", "icon": "⚠️"},
            {"id": "nav-analytics", "label": "Performance & Monthly Summary", "label_kn": "ಮಾಸಿಕ ಸಾಧನೆ ಸಾರಾಂಶ", "path": "#analytics", "icon": "📊"},
            {"id": "nav-profile", "label": "My Profile / Area Details", "label_kn": "ನನ್ನ ವಿವರ ಮತ್ತು ಸೇವಾ ಪ್ರದೇಶ", "path": "#profile", "icon": "👤"},
            {"id": "nav-finder", "label": "Public Finder / Area Lookup", "label_kn": "ಆಶಾ ಕಾರ್ಯಕರ್ತೆ ಹುಡುಕಿ", "path": "#finder", "icon": "🔍"}
        ]

        return {
            "worker_profile": {
                "id": worker["id"],
                "username": worker["username"],
                "full_name": worker["full_name"],
                "badge_id": worker["badge_id"] or worker["id"],
                "role": worker["role"],
                "mobile": worker["mobile"],
                "work_contact": worker["work_contact"] or worker["mobile"],
                "phc_name": worker["phc_name"] or "Primary Health Centre",
                "village": worker["village"] or "Assigned Village",
                "area_name": worker["area_name"] or "Assigned Sector",
                "pincode": worker["pincode"] or "N/A",
                "taluk": worker["taluk"] or "Maddur",
                "district": worker["district"] or "Mandya"
            },
            "metrics": {
                "total_households": total_households,
                "total_population": pop_count,
                "surveys_completed": surveys_completed,
                "surveys_pending": surveys_pending,
                "survey_completion_rate": completion_rate,
                "today_visits_count": today_visits_count,
                "pending_followups_count": pending_followups_count,
                "high_risk_beneficiaries_count": high_risk_count
            },
            "today_visits": parsed_visits,
            "upcoming_followups": parsed_followups,
            "quick_navigation": quick_navigation,
            "timestamp": datetime.now().isoformat()
        }

def admin_list_workers() -> List[Dict[str, Any]]:
    """Lists all registered ASHA workers with coverage and activity metrics."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT 
                u.id, u.username, u.full_name, u.role, u.mobile, u.badge_id,
                u.phc_name, u.work_contact, u.is_verified, u.is_active, u.created_at, u.updated_at,
                u.assigned_area_id,
                a.village, a.area_name, a.pincode, a.taluk, a.district,
                (SELECT COUNT(*) FROM households WHERE area_id = u.assigned_area_id OR created_by_worker_id = u.id) as total_households,
                (SELECT COUNT(*) FROM households WHERE (area_id = u.assigned_area_id OR created_by_worker_id = u.id) AND survey_status = 'completed') as completed_surveys
            FROM users u
            LEFT JOIN areas a ON u.assigned_area_id = a.id
            WHERE u.role = 'asha_worker'
            ORDER BY u.full_name ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]

def admin_register_worker(worker_data: Dict[str, Any], performed_by: str = "USR-ADMIN") -> Dict[str, Any]:
    """Registers a new ASHA worker and assigns an area."""
    with get_db() as conn:
        now_iso = datetime.now().isoformat()
        worker_id = f"USR-ASHA-{uuid.uuid4().hex[:6].upper()}"
        username = worker_data["username"].strip().lower()
        
        existing = conn.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,)).fetchone()
        if existing:
            raise ValidationError(f"Username '{username}' is already in use.")

        badge_id = worker_data.get("badge_id") or f"ASHA-KA-MDY-{uuid.uuid4().hex[:4].upper()}"
        pwd = worker_data.get("password") or "asha123"
        pwd_hash = hash_password(pwd)
        assigned_area_id = worker_data.get("assigned_area_id")

        conn.execute(
            """
            INSERT INTO users (id, username, password_hash, role, full_name, mobile, assigned_area_id,
                               badge_id, phc_name, work_contact, is_verified, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 'asha_worker', ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
            """,
            (worker_id, username, pwd_hash, worker_data["full_name"], worker_data.get("mobile"),
             assigned_area_id, badge_id, worker_data.get("phc_name", "Primary Health Centre"),
             worker_data.get("work_contact", worker_data.get("mobile")), now_iso, now_iso)
        )

        if assigned_area_id:
            conn.execute("UPDATE areas SET assigned_worker_id = ? WHERE id = ?", (worker_id, assigned_area_id))
            conn.execute(
                """
                INSERT INTO worker_area_assignments (id, worker_id, area_id, is_primary, assigned_at)
                VALUES (?, ?, ?, 1, ?)
                """,
                (f"WAA-{uuid.uuid4().hex[:6].upper()}", worker_id, assigned_area_id, now_iso)
            )

        log_audit_action(
            action="WORKER_REGISTERED",
            performed_by=performed_by,
            target_entity="USER",
            target_id=worker_id,
            details=f"Registered ASHA worker {worker_data['full_name']} (Badge: {badge_id}) for area {assigned_area_id}",
            conn=conn
        )

    return get_user_by_id(worker_id)

def admin_update_worker(worker_id: str, updates: Dict[str, Any], performed_by: str = "USR-ADMIN") -> Dict[str, Any]:
    """Updates worker details, activation, verification, or reassigns village/area."""
    with get_db() as conn:
        now_iso = datetime.now().isoformat()
        current = conn.execute("SELECT * FROM users WHERE id = ?", (worker_id,)).fetchone()
        if not current:
            raise NotFoundError(f"Worker '{worker_id}' not found.")

        old_area_id = current["assigned_area_id"]
        new_area_id = updates.get("assigned_area_id", old_area_id)

        full_name = updates.get("full_name", current["full_name"])
        mobile = updates.get("mobile", current["mobile"])
        work_contact = updates.get("work_contact", current["work_contact"])
        badge_id = updates.get("badge_id", current["badge_id"])
        phc_name = updates.get("phc_name", current["phc_name"])
        is_active = updates.get("is_active", current["is_active"])
        is_verified = updates.get("is_verified", current["is_verified"])

        conn.execute(
            """
            UPDATE users SET 
                full_name = ?, mobile = ?, work_contact = ?, badge_id = ?,
                phc_name = ?, assigned_area_id = ?, is_active = ?, is_verified = ?, updated_at = ?
            WHERE id = ?
            """,
            (full_name, mobile, work_contact, badge_id, phc_name, new_area_id, is_active, is_verified, now_iso, worker_id)
        )

        if new_area_id and new_area_id != old_area_id:
            conn.execute("UPDATE areas SET assigned_worker_id = ? WHERE id = ?", (worker_id, new_area_id))
            conn.execute(
                """
                INSERT INTO worker_area_assignments (id, worker_id, area_id, is_primary, assigned_at)
                VALUES (?, ?, ?, 1, ?)
                """,
                (f"WAA-{uuid.uuid4().hex[:6].upper()}", worker_id, new_area_id, now_iso)
            )
            log_audit_action(
                action="AREA_REASSIGNED",
                performed_by=performed_by,
                target_entity="AREA",
                target_id=new_area_id,
                details=f"Reassigned area {new_area_id} from {old_area_id} to worker {worker_id} ({full_name})",
                conn=conn
            )
        else:
            log_audit_action(
                action="WORKER_UPDATED",
                performed_by=performed_by,
                target_entity="USER",
                target_id=worker_id,
                details=f"Updated worker details for {full_name} (Active: {is_active}, Verified: {is_verified})",
                conn=conn
            )

    return get_user_by_id(worker_id)

def admin_reset_worker_password(worker_id: str, new_password: str, performed_by: str = "USR-ADMIN") -> bool:
    """Resets an ASHA worker's password and logs the action."""
    with get_db() as conn:
        now_iso = datetime.now().isoformat()
        current = conn.execute("SELECT id, full_name, username FROM users WHERE id = ?", (worker_id,)).fetchone()
        if not current:
            raise NotFoundError(f"Worker '{worker_id}' not found.")

        new_hash = hash_password(new_password)
        conn.execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?", (new_hash, now_iso, worker_id))

        log_audit_action(
            action="PASSWORD_RESET",
            performed_by=performed_by,
            target_entity="USER",
            target_id=worker_id,
            details=f"Password reset for {current['full_name']} ({current['username']})",
            conn=conn
        )
        return True

def supervisor_get_overview(supervisor_id: str, taluk: Optional[str] = "Maddur") -> Dict[str, Any]:
    """
    Returns taluk-level jurisdiction overview for Health Supervisors:
    active workers, coverage, village survey completion, and identifies unassigned villages.
    """
    with get_db() as conn:
        area_sql = "SELECT * FROM areas"
        params = []
        if taluk:
            area_sql += " WHERE LOWER(taluk) = ?"
            params.append(taluk.strip().lower())
        area_rows = conn.execute(area_sql, params).fetchall()

        total_areas = len(area_rows)
        assigned_areas = [a for a in area_rows if a["assigned_worker_id"]]
        unassigned_areas = [dict(a) for a in area_rows if not a["assigned_worker_id"]]

        workers = conn.execute(
            """
            SELECT u.id, u.full_name, u.badge_id, u.mobile, u.work_contact, u.is_active,
                   a.village, a.area_name, a.pincode,
                   (SELECT COUNT(*) FROM households WHERE area_id = a.id) as total_households,
                   (SELECT COUNT(*) FROM households WHERE area_id = a.id AND survey_status = 'completed') as completed_surveys
            FROM users u
            JOIN areas a ON u.assigned_area_id = a.id
            WHERE u.role = 'asha_worker' AND LOWER(a.taluk) = ?
            ORDER BY a.village, u.full_name
            """,
            (taluk.strip().lower() if taluk else 'maddur',)
        ).fetchall()

        area_ids = [a["id"] for a in area_rows]
        if area_ids:
            placeholders = ",".join("?" * len(area_ids))
            total_hh = conn.execute(f"SELECT COUNT(*) FROM households WHERE area_id IN ({placeholders})", area_ids).fetchone()[0]
            completed_hh = conn.execute(f"SELECT COUNT(*) FROM households WHERE area_id IN ({placeholders}) AND survey_status = 'completed'", area_ids).fetchone()[0]
        else:
            total_hh, completed_hh = 0, 0

        village_map = {}
        for a in area_rows:
            v_name = a["village"]
            if v_name not in village_map:
                village_map[v_name] = {
                    "village": v_name,
                    "taluk": a["taluk"],
                    "district": a["district"],
                    "pincode": a["pincode"],
                    "phc_name": a["phc_name"],
                    "assigned_workers": [],
                    "has_worker": False,
                    "total_households": 0,
                    "completed_surveys": 0
                }
            if a["assigned_worker_id"]:
                village_map[v_name]["has_worker"] = True

        for w in workers:
            v_name = w["village"]
            if v_name in village_map:
                village_map[v_name]["assigned_workers"].append({
                    "id": w["id"],
                    "name": w["full_name"],
                    "badge_id": w["badge_id"],
                    "contact": w["work_contact"]
                })
                village_map[v_name]["total_households"] += w["total_households"]
                village_map[v_name]["completed_surveys"] += w["completed_surveys"]

        audit_logs = conn.execute(
            "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10"
        ).fetchall()

        return {
            "taluk": taluk or "All Taluks",
            "total_areas": total_areas,
            "assigned_areas_count": len(assigned_areas),
            "unassigned_areas_count": len(unassigned_areas),
            "total_workers": len(workers),
            "total_households": total_hh,
            "completed_households": completed_hh,
            "coverage_percentage": round((completed_hh / total_hh * 100), 1) if total_hh > 0 else 0.0,
            "workers": [dict(w) for w in workers],
            "villages_breakdown": list(village_map.values()),
            "unassigned_areas": unassigned_areas,
            "recent_audit_logs": [dict(al) for al in audit_logs],
            "generated_at": datetime.now().isoformat()
        }

def log_audit_action(action: str, performed_by: str, target_entity: str, target_id: str, details: str, conn=None):
    """Writes an administrative or operational event to the audit_logs table."""
    sql = """
        INSERT INTO audit_logs (id, action, performed_by, target_entity, target_id, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = (f"AUD-{uuid.uuid4().hex[:8].upper()}", action, performed_by, target_entity, target_id, details, datetime.now().isoformat())
    if conn is not None:
        conn.execute(sql, params)
    else:
        with get_db() as c:
            c.execute(sql, params)

def get_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent audit logs for administrators."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

# ============================================================================
# VOICE RECORDS (PHASE 1 -> PHASE 2 PERSISTENCE)
# ============================================================================

def save_voice_record(data: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Persists a voice transcription and extracted structured payload into voice_records table.
    Enforces record ID stability across phases and detects duplicates.
    """
    with get_db() as conn:
        now_iso = datetime.now().isoformat()
        transcript = str(data.get("transcript") or "").strip()
        language = str(data.get("language") or "kn-IN").strip()
        worker_id = (user.get("id") if user else None) or data.get("worker_id")
        form_type = data.get("form_type") or "clinical_visit"
        record_id = data.get("record_id") or data.get("id")
        if not record_id or record_id.startswith("DRAFT-"):
            record_id = f"REC-{uuid.uuid4().hex[:8].upper()}"

        sub_hash = hashlib.sha256(f"{worker_id or 'anon'}:{transcript}:{form_type}".encode()).hexdigest()
        existing = conn.execute("SELECT * FROM voice_records WHERE submission_hash = ? OR id = ?", (sub_hash, record_id)).fetchone()
        if existing:
            rec = dict(existing)
            if rec.get("structured_data"):
                try:
                    rec["structured_data"] = json.loads(rec["structured_data"])
                except Exception:
                    pass
            return {"status": "success", "duplicate": True, "record": rec}

        structured_data = data.get("report") or data.get("household_data") or data.get("extracted_report") or data.get("structured_data")
        str_data_json = json.dumps(structured_data) if structured_data else None

        conn.execute(
            """
            INSERT INTO voice_records 
            (id, session_id, worker_id, form_type, transcript, language, structured_data, confidence_score, status, submission_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (record_id, data.get("session_id"), worker_id, form_type, transcript, language,
             str_data_json, float(data.get("confidence_score", 1.0)), data.get("status", "completed"),
             sub_hash, now_iso, now_iso)
        )

        return {
            "status": "success",
            "duplicate": False,
            "record": {
                "id": record_id,
                "session_id": data.get("session_id"),
                "worker_id": worker_id,
                "form_type": form_type,
                "transcript": transcript,
                "language": language,
                "structured_data": structured_data,
                "confidence_score": float(data.get("confidence_score", 1.0)),
                "status": data.get("status", "completed"),
                "created_at": now_iso
            }
        }

def get_voice_records(worker_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves saved voice records from the SQLite database."""
    with get_db() as conn:
        if worker_id:
            rows = conn.execute(
                "SELECT * FROM voice_records WHERE worker_id = ? ORDER BY created_at DESC LIMIT ?",
                (worker_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM voice_records ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        
        result = []
        for r in rows:
            d = dict(r)
            if d.get("structured_data"):
                try:
                    d["structured_data"] = json.loads(d["structured_data"])
                except Exception:
                    pass
            result.append(d)
        return result

def get_voice_record_by_id(record_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single voice record by ID."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM voice_records WHERE id = ?", (record_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("structured_data"):
            try:
                d["structured_data"] = json.loads(d["structured_data"])
            except Exception:
                pass
        return d

# ============================================================================
# SELF-SERVICE ASHA WORKER REGISTRATION
# ============================================================================

def register_worker_self_service(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Self-service registration for ASHA workers.
    Creates or reuses geographic area, generates official badge ID, hashes password,
    creates user account, and assigns primary area in persistent SQLite database.
    """
    with get_db() as conn:
        now_iso = datetime.now().isoformat()
        username = str(data["username"]).strip().lower()
        
        existing = conn.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,)).fetchone()
        if existing:
            raise ValidationError(f"Username '{username}' is already registered. Please choose another username or log in.")

        worker_id = f"USR-ASHA-{uuid.uuid4().hex[:6].upper()}"
        full_name = str(data["full_name"]).strip()
        mobile = str(data.get("mobile") or "").strip() or None
        village = str(data.get("village") or "Rampur").strip()
        pincode = str(data.get("pincode") or "571428").strip()
        taluk = str(data.get("taluk") or "Maddur").strip()
        district = str(data.get("district") or "Mandya").strip()
        state = str(data.get("state") or "Karnataka").strip()
        phc_name = str(data.get("phc_name") or "Primary Health Centre").strip()
        sector = str(data.get("sector") or f"Sector {village}").strip()
        badge_id = data.get("badge_id") or f"ASHA-KA-{pincode[:3]}-{uuid.uuid4().hex[:3].upper()}"
        pwd = data.get("password") or "asha123"
        pwd_hash = hash_password(pwd)

        # Check or create area
        area_row = conn.execute(
            "SELECT id FROM areas WHERE LOWER(village) = ? AND pincode = ?",
            (village.lower(), pincode)
        ).fetchone()

        if area_row:
            area_id = area_row["id"]
        else:
            area_id = f"AREA-{uuid.uuid4().hex[:6].upper()}"
            conn.execute(
                """
                INSERT INTO areas (id, state, district, taluk, village, area_name, pincode, phc_name, assigned_worker_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (area_id, state, district, taluk, village, sector, pincode, phc_name, worker_id, now_iso, now_iso)
            )

        # Insert user
        conn.execute(
            """
            INSERT INTO users 
            (id, username, password_hash, role, full_name, mobile, assigned_area_id,
             badge_id, phc_name, work_contact, is_verified, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 'asha_worker', ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
            """,
            (worker_id, username, pwd_hash, full_name, mobile, area_id,
             badge_id, phc_name, mobile, now_iso, now_iso)
        )

        # Link area
        conn.execute(
            """
            INSERT OR REPLACE INTO worker_area_assignments (id, worker_id, area_id, is_primary, assigned_at)
            VALUES (?, ?, ?, 1, ?)
            """,
            (f"WAA-{uuid.uuid4().hex[:8].upper()}", worker_id, area_id, now_iso)
        )

        # Audit log
        conn.execute(
            """
            INSERT INTO audit_logs (id, action, performed_by, target_entity, target_id, details, created_at)
            VALUES (?, 'WORKER_SELF_REGISTERED', ?, 'USER', ?, ?, ?)
            """,
            (f"AUD-{uuid.uuid4().hex[:8].upper()}", worker_id, worker_id, f"Registered new ASHA worker {full_name} ({badge_id})", now_iso)
        )

        user_obj = {
            "id": worker_id,
            "username": username,
            "role": "asha_worker",
            "full_name": full_name,
            "mobile": mobile,
            "work_contact": mobile,
            "badge_id": badge_id,
            "assigned_area_id": area_id,
            "assigned_village": village,
            "assigned_pincode": pincode,
            "taluk": taluk,
            "district": district,
            "phc_name": phc_name,
            "sector": sector,
            "is_verified": 1,
            "is_active": 1,
            "created_at": now_iso
        }
        return user_obj

