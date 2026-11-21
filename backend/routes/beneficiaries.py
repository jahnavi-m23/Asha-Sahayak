"""
Beneficiaries API Router for ASHA Sahayak Phase 3.
Provides beneficiary listing, search by ID/name, and detailed visit history.
"""

from typing import List, Optional, Any, Dict
from fastapi import APIRouter, HTTPException, Query, status

from backend.database.crud import (
    get_beneficiaries,
    get_beneficiary_details,
)

router = APIRouter(prefix="/api/beneficiaries", tags=["Beneficiaries"])

@router.get("", response_model=List[Dict[str, Any]])
def list_beneficiaries(
    search: Optional[str] = Query(None, description="Search term for beneficiary ID, name, or village/ward"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Returns list of beneficiaries with total visits and active follow-up counts.
    Supports real-time search by Beneficiary ID (e.g. BNF-2041).
    """
    try:
        return get_beneficiaries(search=search, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query beneficiaries: {str(e)}"
        )

@router.get("/{beneficiary_id}")
def get_beneficiary_by_id(beneficiary_id: str):
    """
    Returns full beneficiary record, previous visits history,
    relevant vaccinations, and upcoming/overdue follow-ups.
    """
    try:
        details = get_beneficiary_details(beneficiary_id)
        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Beneficiary with ID '{beneficiary_id}' not found."
            )
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve beneficiary details: {str(e)}"
        )
