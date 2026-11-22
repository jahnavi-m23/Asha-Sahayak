"""
Visits API Router for ASHA Sahayak Phase 3.
Accepts Phase 2 worker-confirmed records, persists them, prevents duplicates,
and serves visit history.
"""

from typing import List, Optional, Any, Dict
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database.crud import (
    save_confirmed_visit,
    get_visits,
    DuplicateVisitError,
    ValidationError,
)

router = APIRouter(prefix="/api/visits", tags=["Visits"])

class ConfirmedVisitRequest(BaseModel):
    """
    Agreed schema matching Phase 2 output:
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
    beneficiary_id: str = Field(..., description="Unique Beneficiary ID, e.g. BNF-2041")
    beneficiary_name: Optional[str] = Field(None, description="Beneficiary Full Name")
    age: Optional[int] = Field(None, description="Beneficiary Age in Years")
    visit_type: str = Field(..., description="Type of healthcare visit e.g. 'Newborn home visit'")
    weight: Optional[str] = Field(None, description="Weight measurement e.g. '3.2 kg'")
    blood_pressure: Optional[str] = Field(None, description="Blood pressure measurement e.g. '120/80'")
    gestational_age: Optional[str] = Field(None, description="Gestational age e.g. '28 weeks'")
    pregnancy_status: Optional[str] = Field(None, description="Pregnancy or delivery status")
    vaccinations_due: Optional[List[str]] = Field(default_factory=list, description="List of vaccinations due")
    symptoms_reported: Optional[List[str]] = Field(default_factory=list, description="List of reported symptoms")
    negated_symptoms: Optional[List[str]] = Field(default_factory=list, description="List of ruled-out/negated symptoms")
    next_visit_date: Optional[str] = Field(None, description="Scheduled follow-up date (YYYY-MM-DD) or null")
    danger_signs: Optional[List[str]] = Field(default_factory=list, description="Predefined danger signs from Phase 2")
    referral_required: bool = Field(False, description="Flag indicating whether referral to PHC is needed")
    confirmation_status: str = Field("confirmed", description="Must be 'confirmed' to save")
    visit_date: Optional[str] = Field(None, description="Optional visit date YYYY-MM-DD")
    worker_id: Optional[str] = Field(None, description="ASHA Worker ID")
    raw_transcript: Optional[str] = Field(None, description="Raw voice transcript")

@router.post("/confirm", status_code=status.HTTP_201_CREATED)
def confirm_and_save_visit(visit_in: ConfirmedVisitRequest):
    """
    Saves a worker-confirmed visit record into the SQLite database.
    Rejects any unconfirmed or pending records.
    Prevents duplicate submissions.
    Automatically links to follow-ups if next_visit_date is specified.
    """
    # Enforce confirmed status rule
    if visit_in.confirmation_status.lower() != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Validation Error: Only confirmed visit records can be saved. "
                f"Received confirmation_status='{visit_in.confirmation_status}'."
            )
        )

    payload = visit_in.model_dump()
    try:
        saved_record = save_confirmed_visit(payload)
        return saved_record
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except DuplicateVisitError as dve:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(dve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal database error while saving visit: {str(e)}"
        )

@router.get("", response_model=List[Dict[str, Any]])
def list_visits(
    beneficiary_id: Optional[str] = Query(None, description="Filter visits by beneficiary ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Lists visit records with beneficiary metadata, parsed vaccinations, and referral status.
    """
    try:
        return get_visits(beneficiary_id=beneficiary_id, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query visits: {str(e)}"
        )
