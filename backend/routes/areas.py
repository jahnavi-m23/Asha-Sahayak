"""
Geographical Areas API Router for ASHA Sahayak
Manages state, district, taluk, village, area names, and PIN codes.
Enforces role-based area visibility.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from backend.database.crud import get_areas, create_area, get_area_by_id
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/api/areas", tags=["Areas & Geography"])

class AreaCreateRequest(BaseModel):
    state: str = Field("Karnataka", description="State name")
    district: str = Field(..., description="District name e.g. Mandya, Ramanagara")
    taluk: str = Field(..., description="Taluk name e.g. Maddur, Channapatna")
    village: str = Field(..., description="Village or Locality name e.g. Rampur, Kalyanpur")
    area_name: str = Field(..., description="Specific area or ward e.g. Ward 4 - Anganwadi 2")
    pincode: str = Field(..., description="6-digit postal PIN code e.g. 571428")
    assigned_worker_id: Optional[str] = Field(None, description="Assigned ASHA worker user ID")

@router.get("", response_model=List[Dict[str, Any]])
def list_areas(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns geographical areas.
    ASHA workers only see their designated assigned area.
    Administrators and Health Supervisors can see and manage all areas.
    """
    return get_areas(user=current_user)

@router.post("", status_code=status.HTTP_201_CREATED)
def add_area(area_in: AreaCreateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Creates a new geographical area (Administrator only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators are authorized to add new geographical areas."
        )

    return create_area(area_in.model_dump())

@router.get("/{area_id}")
def get_area(area_id: str):
    """Retrieves area details by ID."""
    area = get_area_by_id(area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found.")
    return area
