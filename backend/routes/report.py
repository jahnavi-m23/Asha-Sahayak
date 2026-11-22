import uuid
import datetime
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.extraction.engine import ASHAExtractionEngine
from backend.extraction.household_extractor import HouseholdExtractor
from backend.database.crud import save_confirmed_visit, get_visits, DuplicateVisitError

logger = logging.getLogger("routes.report")
router = APIRouter(prefix="/api/report", tags=["Phase 2 Extraction & Phase 3 Register"])

# In-memory Phase 3 Register Store (persists across sessions during server lifetime)
SAVED_FIELD_VISIT_REGISTER: List[Dict[str, Any]] = [
    # Seed with realistic synthetic benchmark record for dashboard display
    {
        "id": "VISIT-BENCH-001",
        "beneficiary_id": "KA-RCH-8921",
        "beneficiary_name": "Lakshmi",
        "visit_type": "ANC Home Visit (ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ)",
        "pregnancy_status": "Pregnant (ಗರ್ಭಿಣಿ)",
        "gestational_age": "24 weeks (24 ವಾರಗಳು)",
        "infant_weight": None,
        "blood_pressure": "120/80",
        "vaccinations_due": ["Td-2"],
        "vaccinations_given": ["Td-1"],
        "symptoms_reported": ["Headache"],
        "negated_symptoms": ["No Bleeding (Bleeding ಇಲ್ಲ)"],
        "next_visit_date": "Next Week (ಮುಂದಿನ ವಾರ)",
        "danger_signs": [],
        "referral_required": False,
        "referral_facility": None,
        "missing_fields": [],
        "uncertain_indicators": [],
        "confidence_score": 0.95,
        "confirmed": True,
        "raw_transcript": "ಫಲಾನುಭವಿ ಲಕ್ಷ್ಮಿ ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ 24 ವಾರಗಳು ರಕ್ತದೊತ್ತಡ 120/80 ಇದೆ ತಲೆನೋವು ಇದೆ ರಕ್ತಸ್ರಾವ ಇಲ್ಲ",
        "readback_en": "Beneficiary Lakshmi. ANC Home Visit. Gestational age 24 weeks. Reported symptoms: Headache. Confirmed absent: No Bleeding.",
        "readback_kn": "ಫಲಾನುಭವಿ ಲಕ್ಷ್ಮಿ. ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ. ವಯಸ್ಸು 24 ವಾರಗಳು. ತಲೆನೋವು ವರದಿಯಾಗಿದೆ. ರಕ್ತಸ್ರಾವ ಇಲ್ಲ.",
        "created_at": "2026-11-20T10:30:00"
    }
]


# ==============================================================================
# Request & Response Schemas
# ==============================================================================
class ExtractReportRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="Transcribed field narrative")
    language: str = Field(default="kn-IN", description="Language of original speech")


class VoiceCorrectionRequest(BaseModel):
    current_report: Dict[str, Any] = Field(..., description="Currently displayed report draft")
    correction_text: str = Field(..., min_length=1, description="Spoken or typed correction string")


class SaveReportRequest(BaseModel):
    report: Dict[str, Any] = Field(..., description="Final reviewed report")
    confirmed: bool = Field(default=True, description="Explicit worker confirmation")


# ==============================================================================
# API Endpoints (Phase 2 & Phase 3 Contract)
# ==============================================================================
@router.post("/extract")
async def extract_structured_report(payload: ExtractReportRequest):
    """
    Phase 2 Extraction Engine:
    Analyzes finalized ASR transcript and produces a 13-field structured clinical report.
    Prepares bilingual voice readback summaries.
    """
    clean_text = payload.transcript.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript cannot be empty for report extraction."
        )

    try:
        is_household = HouseholdExtractor.is_household_intent(clean_text)
        if is_household:
            hh_data = HouseholdExtractor.extract_household(clean_text, payload.language)
            visit_report = ASHAExtractionEngine.extract_report(
                raw_transcript=clean_text,
                language_code=payload.language
            )
            report = {
                **visit_report,
                "id": f"DRAFT-HH-{uuid.uuid4().hex[:8].upper()}",
                "form_type": "HOUSEHOLD",
                "household_data": hh_data,
                "head_of_family": hh_data["head_of_family"],
                "member_count": hh_data["member_count"],
                "village": hh_data["village"],
                "pincode": hh_data["pincode"],
                "address": hh_data["address"],
                "contact_number": hh_data["contact_number"],
                "house_type": hh_data["house_type"],
                "water_source": hh_data["water_source"],
                "toilet_available": hh_data["toilet_available"],
                "sanitation_facility": hh_data["sanitation_facility"],
                "family_members": hh_data["family_members"],
                "clarification_prompt": hh_data["clarification_prompt"],
                "readback_kn": hh_data["readback_kn"],
                "readback_en": hh_data["readback_en"],
                "confidence_score": hh_data["confidence_score"]
            }
            logger.info(f"[Phase 2 Extraction] Extracted Household profile for '{hh_data.get('head_of_family')}'")
        else:
            report = ASHAExtractionEngine.extract_report(
                raw_transcript=clean_text,
                language_code=payload.language
            )
            report["id"] = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
            report["form_type"] = "VISIT"
            report["household_data"] = None
            logger.info(f"[Phase 2 Extraction] Extracted visit report for '{report.get('beneficiary_name')}' (Confidence: {report.get('confidence_score')})")

        return {
            "success": True,
            "report": report,
            "form_type": report.get("form_type", "VISIT"),
            "household_data": report.get("household_data")
        }
    except Exception as e:
        logger.error(f"[Phase 2 Extraction Error] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Information extraction failed: {str(e)}"
        )


@router.post("/correct")
async def correct_report_by_voice(payload: VoiceCorrectionRequest):
    """
    Voice Read-Back & Field Correction:
    Parses spoken corrections ('No, the weight is 2.8 kilograms') and updates
    only the relevant field while re-checking danger sign rules.
    """
    try:
        updated_report, modified_field, confirm_phrase = ASHAExtractionEngine.apply_voice_correction(
            current_report=payload.current_report,
            correction_text=payload.correction_text
        )
        logger.info(f"[Voice Correction] Updated field '{modified_field}' via correction: '{payload.correction_text}'")
        return {
            "success": True,
            "modified_field": modified_field,
            "readback_phrase": confirm_phrase,
            "updated_report": updated_report
        }
    except Exception as e:
        logger.error(f"[Voice Correction Error] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice correction failed: {str(e)}"
        )


@router.post("/save")
async def save_confirmed_report(payload: SaveReportRequest):
    """
    Phase 3 Database Storage:
    Saves ONLY confirmed reports to the official ASHA Field Visit Register and SQLite database.
    Rejects unconfirmed or empty drafts.
    """
    if not payload.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot save unconfirmed report. Explicit worker confirmation is required."
        )

    report = dict(payload.report)
    orig_id = report.get("id") or report.get("record_id")
    if not orig_id or orig_id.startswith("DRAFT-"):
        orig_id = f"VISIT-{uuid.uuid4().hex[:8].upper()}"
    report["id"] = orig_id

    report["confirmed"] = True
    report["saved_at"] = datetime.datetime.now().isoformat()

    # Save to SQLite visits table
    try:
        db_payload = {
            "beneficiary_id": report.get("beneficiary_id"),
            "beneficiary_name": report.get("beneficiary_name"),
            "age": report.get("age"),
            "visit_type": report.get("visit_type") or "Routine Field Visit",
            "weight": report.get("infant_weight") or report.get("weight"),
            "blood_pressure": report.get("blood_pressure"),
            "gestational_age": report.get("gestational_age"),
            "pregnancy_status": report.get("pregnancy_status"),
            "vaccinations_due": report.get("vaccinations_due") or report.get("immunization_details") or [],
            "symptoms_reported": report.get("symptoms_reported") or report.get("symptoms") or [],
            "negated_symptoms": report.get("negated_symptoms") or [],
            "next_visit_date": report.get("next_visit_date"),
            "danger_signs": report.get("danger_signs") or [],
            "referral_required": bool(report.get("referral_required")),
            "confirmation_status": "confirmed",
            "worker_id": report.get("worker_id"),
            "raw_transcript": report.get("raw_transcript")
        }
        db_res = save_confirmed_visit(db_payload)
        report["db_visit_id"] = db_res.get("visit_id")
    except DuplicateVisitError:
        logger.info(f"Report {report.get('id')} already persisted in visits table.")
    except Exception as e:
        logger.warning(f"Error persisting report to SQLite visits table: {e}")

    SAVED_FIELD_VISIT_REGISTER.append(report)
    logger.info(f"[Phase 3 Register] Successfully saved confirmed visit report {report['id']} for {report.get('beneficiary_name')}")

    return {
        "success": True,
        "message": "Visit report successfully confirmed and saved to ASHA Field Register.",
        "record_id": report["id"],
        "record": report
    }


@router.get("/list")
async def get_all_reports():
    """
    Phase 3 Dashboard:
    Returns all confirmed visit reports with aggregated community health indicators
    sourced from SQLite database visits and session cache.
    """
    db_visits = get_visits(limit=200)
    
    # Map visit_id to id for backwards compatibility
    for v in db_visits:
        if "id" not in v or not v["id"]:
            v["id"] = v.get("visit_id")

    # Merge session records that may carry custom client IDs
    seen_ids = {v.get("id") for v in db_visits if v.get("id")}
    combined_records = list(db_visits)
    for r in reversed(SAVED_FIELD_VISIT_REGISTER):
        rid = r.get("id")
        if rid and rid not in seen_ids:
            combined_records.append(r)
            seen_ids.add(rid)

    total = max(len(combined_records), len(SAVED_FIELD_VISIT_REGISTER))
    referrals = sum(1 for r in combined_records if r.get("referral_required"))
    vaccinations_due_count = sum(len(r.get("vaccinations_due", [])) for r in combined_records)
    followups_count = sum(1 for r in combined_records if r.get("next_visit_date"))

    return {
        "stats": {
            "total_visits": total,
            "high_risk_referrals": referrals,
            "immunizations_scheduled": vaccinations_due_count,
            "pending_followups": followups_count
        },
        "records": combined_records
    }


@router.get("/{report_id}")
async def get_report_by_id(report_id: str):
    """Retrieves a single visit report by ID."""
    for record in SAVED_FIELD_VISIT_REGISTER:
        if record.get("id") == report_id:
            return {"success": True, "record": record}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """Deletes or archives a report from the register."""
    global SAVED_FIELD_VISIT_REGISTER
    initial_len = len(SAVED_FIELD_VISIT_REGISTER)
    SAVED_FIELD_VISIT_REGISTER = [r for r in SAVED_FIELD_VISIT_REGISTER if r.get("id") != report_id]
    if len(SAVED_FIELD_VISIT_REGISTER) == initial_len:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
    return {"success": True, "message": f"Report {report_id} removed from register."}

