"""
Validation helpers for ASHA Sahayak Phase 3.
Ensures Phase 2 JSON contracts, rejects unconfirmed visits, and validates dates.
"""

import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def parse_relative_date(date_str: str) -> Optional[str]:
    """Converts spoken/relative date strings like 'Next Week' to YYYY-MM-DD."""
    if not date_str:
        return None
    s = str(date_str).strip()
    if DATE_REGEX.match(s):
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except ValueError:
            return None

    s_lower = s.lower()
    now = datetime.now()
    if "next week" in s_lower or "ಮುಂದಿನ ವಾರ" in s:
        return (now + timedelta(days=7)).strftime("%Y-%m-%d")
    if "next month" in s_lower or "ಮುಂದಿನ ತಿಂಗಳು" in s:
        return (now + timedelta(days=30)).strftime("%Y-%m-%d")
    
    m_days = re.search(r"(\d+)\s*(?:days?|ದಿನ)", s_lower)
    if m_days:
        try:
            days = int(m_days.group(1))
            return (now + timedelta(days=days)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

def validate_confirmed_visit_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validates the Phase 2 confirmed visit payload according to agreed schema.
    Returns: (is_valid: bool, error_message: str | None, sanitized_data: dict)
    """
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object", {}

    # 1. Beneficiary ID validation (Auto-generate clean ID if missing or draft)
    raw_id = str(data.get("beneficiary_id") or "").strip().upper()
    if not raw_id or raw_id in ("NONE", "NULL", "UNDEFINED") or raw_id.startswith("DRAFT-"):
        beneficiary_id = f"BNF-{uuid.uuid4().hex[:6].upper()}"
    else:
        beneficiary_id = re.sub(r"[^A-Z0-9\-_]", "", raw_id)
        if len(beneficiary_id) < 3:
            beneficiary_id = f"BNF-{uuid.uuid4().hex[:6].upper()}"

    # 2. Visit type validation
    visit_type = str(data.get("visit_type", "")).strip() or "Routine Field Visit"

    # 3. Confirmation status check - MUST BE 'confirmed'
    confirmation_status = str(data.get("confirmation_status", "")).strip().lower()
    if confirmation_status != "confirmed":
        return False, (
            f"Only worker-confirmed visit records can be saved. "
            f"Received confirmation_status='{data.get('confirmation_status')}'."
        ), {}

    # 4. Weight (optional, string or number, check aliases)
    raw_weight = data.get("weight") or data.get("infant_weight")
    weight = str(raw_weight).strip() if raw_weight is not None else None

    # 5. Vaccinations due (list of strings, check aliases)
    raw_vaccinations = data.get("vaccinations_due") or data.get("immunization_details") or []
    if raw_vaccinations is None:
        vaccinations_due = []
    elif isinstance(raw_vaccinations, list):
        vaccinations_due = [str(v).strip() for v in raw_vaccinations if str(v).strip()]
    elif isinstance(raw_vaccinations, str) and raw_vaccinations.strip():
        vaccinations_due = [raw_vaccinations.strip()]
    else:
        return False, "vaccinations_due must be a list of vaccine name strings", {}

    # 6. Next visit date validation (nullable, converts relative phrases to YYYY-MM-DD)
    raw_next_date = data.get("next_visit_date")
    next_visit_date = None
    if raw_next_date:
        next_visit_date = parse_relative_date(str(raw_next_date))

    # 7. Danger signs (list of strings, predefined from Phase 2)
    raw_danger = data.get("danger_signs", [])
    if raw_danger is None:
        danger_signs = []
    elif isinstance(raw_danger, list):
        danger_signs = [d.get("name", str(d)) if isinstance(d, dict) else str(d).strip() for d in raw_danger if d]
    elif isinstance(raw_danger, str) and raw_danger.strip():
        danger_signs = [raw_danger.strip()]
    else:
        return False, "danger_signs must be a list of strings", {}

    # 8. Referral required (boolean)
    raw_referral = data.get("referral_required", False)
    if isinstance(raw_referral, bool):
        referral_required = raw_referral
    elif isinstance(raw_referral, str):
        referral_required = raw_referral.lower() in ("true", "1", "yes")
    elif isinstance(raw_referral, int):
        referral_required = bool(raw_referral)
    else:
        referral_required = False

    # Optional visit_date override (defaults to current local date if not specified)
    raw_visit_date = data.get("visit_date")
    if raw_visit_date and DATE_REGEX.match(str(raw_visit_date).strip()):
        visit_date = str(raw_visit_date).strip()
    else:
        visit_date = datetime.now().strftime("%Y-%m-%d")

    # Additional Phase 2 extraction fields mapped to Database columns
    beneficiary_name = data.get("beneficiary_name") or data.get("name")
    if beneficiary_name:
        beneficiary_name = str(beneficiary_name).strip()
    
    age = None
    raw_age = data.get("age") or data.get("beneficiary_age")
    if raw_age is not None:
        try:
            age = int(re.sub(r"[^\d]", "", str(raw_age)))
        except (ValueError, TypeError):
            age = None

    blood_pressure = str(data.get("blood_pressure")).strip() if data.get("blood_pressure") else None
    gestational_age = str(data.get("gestational_age")).strip() if data.get("gestational_age") else None
    pregnancy_status = str(data.get("pregnancy_status")).strip() if data.get("pregnancy_status") else None

    raw_symptoms = data.get("symptoms_reported") or data.get("symptoms") or []
    if isinstance(raw_symptoms, list):
        symptoms_reported = [str(s).strip() for s in raw_symptoms if str(s).strip()]
    elif isinstance(raw_symptoms, str) and raw_symptoms.strip():
        symptoms_reported = [raw_symptoms.strip()]
    else:
        symptoms_reported = []

    raw_negated = data.get("negated_symptoms") or []
    if isinstance(raw_negated, list):
        negated_symptoms = [str(n).strip() for n in raw_negated if str(n).strip()]
    elif isinstance(raw_negated, str) and raw_negated.strip():
        negated_symptoms = [raw_negated.strip()]
    else:
        negated_symptoms = []

    worker_id = str(data.get("worker_id")).strip() if data.get("worker_id") else None
    raw_transcript = str(data.get("raw_transcript") or data.get("transcript") or "").strip() or None

    sanitized = {
        "beneficiary_id": beneficiary_id,
        "beneficiary_name": beneficiary_name,
        "age": age,
        "visit_type": visit_type,
        "weight": weight,
        "blood_pressure": blood_pressure,
        "gestational_age": gestational_age,
        "pregnancy_status": pregnancy_status,
        "vaccinations_due": vaccinations_due,
        "symptoms_reported": symptoms_reported,
        "negated_symptoms": negated_symptoms,
        "next_visit_date": next_visit_date,
        "danger_signs": danger_signs,
        "referral_required": referral_required,
        "confirmation_status": "confirmed",
        "visit_date": visit_date,
        "worker_id": worker_id,
        "raw_transcript": raw_transcript
    }
    return True, None, sanitized
