"""
Validation helpers for ASHA Sahayak Phase 3.
Ensures Phase 2 JSON contracts, rejects unconfirmed visits, and validates dates.
"""

import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def validate_confirmed_visit_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validates the Phase 2 confirmed visit payload according to agreed schema.
    Returns: (is_valid: bool, error_message: str | None, sanitized_data: dict)
    """
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object", {}

    # 1. Beneficiary ID validation
    beneficiary_id = str(data.get("beneficiary_id", "")).strip().upper()
    if not beneficiary_id:
        return False, "beneficiary_id is required and cannot be empty", {}
    if not re.match(r"^[A-Z0-9\-_]{3,20}$", beneficiary_id):
        return False, "beneficiary_id must be 3-20 alphanumeric characters (e.g., BNF-2041)", {}

    # 2. Visit type validation
    visit_type = str(data.get("visit_type", "")).strip()
    if not visit_type:
        return False, "visit_type is required and cannot be empty", {}

    # 3. Confirmation status check - MUST BE 'confirmed'
    confirmation_status = str(data.get("confirmation_status", "")).strip().lower()
    if confirmation_status != "confirmed":
        return False, (
            f"Only worker-confirmed visit records can be saved. "
            f"Received confirmation_status='{data.get('confirmation_status')}'."
        ), {}

    # 4. Weight (optional, string or number)
    raw_weight = data.get("weight")
    weight = str(raw_weight).strip() if raw_weight is not None else None

    # 5. Vaccinations due (list of strings)
    raw_vaccinations = data.get("vaccinations_due", [])
    if raw_vaccinations is None:
        vaccinations_due = []
    elif isinstance(raw_vaccinations, list):
        vaccinations_due = [str(v).strip() for v in raw_vaccinations if str(v).strip()]
    elif isinstance(raw_vaccinations, str) and raw_vaccinations.strip():
        vaccinations_due = [raw_vaccinations.strip()]
    else:
        return False, "vaccinations_due must be a list of vaccine name strings", {}

    # 6. Next visit date validation (nullable, do NOT invent dates)
    raw_next_date = data.get("next_visit_date")
    next_visit_date = None
    if raw_next_date:
        next_date_str = str(raw_next_date).strip()
        if not DATE_REGEX.match(next_date_str):
            return False, "next_visit_date must be in YYYY-MM-DD format if provided, or null", {}
        try:
            # Check valid calendar date
            datetime.strptime(next_date_str, "%Y-%m-%d")
            next_visit_date = next_date_str
        except ValueError:
            return False, f"Invalid calendar date for next_visit_date: {next_date_str}", {}

    # 7. Danger signs (list of strings, predefined from Phase 2)
    raw_danger = data.get("danger_signs", [])
    if raw_danger is None:
        danger_signs = []
    elif isinstance(raw_danger, list):
        danger_signs = [str(d).strip() for d in raw_danger if str(d).strip()]
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

    sanitized = {
        "beneficiary_id": beneficiary_id,
        "visit_type": visit_type,
        "weight": weight,
        "vaccinations_due": vaccinations_due,
        "next_visit_date": next_visit_date,
        "danger_signs": danger_signs,
        "referral_required": referral_required,
        "confirmation_status": "confirmed",
        "visit_date": visit_date,
    }
    return True, None, sanitized
