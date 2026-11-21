"""
Follow-ups API Router for ASHA Sahayak Phase 3.
Manages upcoming, overdue, and completed follow-ups, allowing authorized workers
to update visit statuses without inventing arbitrary dates.
"""

from typing import List, Optional, Any, Dict
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database.crud import (
    get_followups,
    update_followup_status,
    ValidationError,
    NotFoundError,
)

router = APIRouter(prefix="/api/followups", tags=["Follow-ups"])

class FollowupStatusUpdate(BaseModel):
    status: str = Field(..., description="Target status: upcoming, overdue, completed, or cancelled")
    worker_notes: Optional[str] = Field(None, description="Notes recorded by ASHA worker")
    worker_id: Optional[str] = Field("ASHA-Worker", description="Authorized worker ID")

@router.get("", response_model=List[Dict[str, Any]])
def list_followups(
    status: Optional[str] = Query(None, description="Filter: upcoming, overdue, pending, completed, cancelled")
):
    """
    Retrieves follow-ups. Automatically evaluates scheduled dates to flag overdue items.
    """
    try:
        return get_followups(status_filter=status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query follow-ups: {str(e)}"
        )

@router.patch("/{followup_id}/status")
def change_followup_status(followup_id: str, update_in: FollowupStatusUpdate):
    """
    Allows authorized ASHA workers to update the status of a scheduled follow-up
    and document notes from field visits.
    """
    try:
        updated = update_followup_status(
            followup_id=followup_id,
            new_status=update_in.status,
            worker_notes=update_in.worker_notes,
            worker_id=update_in.worker_id or "ASHA-Worker"
        )
        return updated
    except NotFoundError as nfe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(nfe)
        )
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update follow-up: {str(e)}"
        )
