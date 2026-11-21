"""
Households & Family Survey API Router for ASHA Sahayak
Manages Household Registration, Multi-Member Family Surveys, Configurable Health Profiling,
Area Scoping, and Dashboard Analytics.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import date
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field, field_validator

from backend.database.crud import (
    get_households,
    get_household_details,
    register_household_and_survey,
    update_household_and_survey,
    delete_household,
    add_family_member,
    update_family_member,
    delete_family_member,
    get_survey_analytics,
    DuplicateHouseholdError,
    ValidationError,
    NotFoundError,
    UnauthorizedAccessError
)
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/api/households", tags=["Households & Family Survey"])

# Member Health Data Schema
class FamilyMemberSchema(BaseModel):
    id: Optional[str] = Field(None, description="Existing member ID if modifying")
    full_name: str = Field("Family Member", description="Full Name of the family member")
    age: Union[int, str] = Field(0, description="Age in years (number or numeric string)")
    gender: str = Field("Female", description="Gender: Male, Female, Other")
    dob: Optional[str] = Field(None, description="Date of birth YYYY-MM-DD")
    relationship: str = Field("Self / Head", description="Relationship with family head")
    mobile: Optional[str] = Field(None, description="Contact mobile number")
    occupation: Optional[str] = Field(None, description="Current occupation")
    education: Optional[str] = Field(None, description="Education level")
    marital_status: Optional[str] = Field("Married", description="Marital status")
    
    # Health information
    is_pregnant: bool = Field(False, description="Is currently pregnant")
    pregnancy_trimester: Optional[str] = Field(None, description="Trimester if pregnant")
    is_lactating: bool = Field(False, description="Is lactating mother")
    lactating_child_age_months: Optional[int] = Field(None, description="Child age in months")
    is_child_under_5: bool = Field(False, description="Is child under 5 years")
    requires_immunization: bool = Field(False, description="Requires routine immunization")
    immunization_due: Optional[str] = Field(None, description="Vaccines due")
    is_elderly: bool = Field(False, description="Is elderly person 60+")
    has_disability: bool = Field(False, description="Has physical or intellectual disability")
    disability_type: Optional[str] = Field(None, description="Type of disability")
    chronic_conditions: Optional[str] = Field("None", description="Hypertension, Diabetes, Asthma, etc.")
    current_medications: Optional[str] = Field(None, description="Ongoing medications")
    recent_checkup_date: Optional[str] = Field(None, description="Date of last health checkup")
    nutritional_status: Optional[str] = Field("Normal", description="Normal, MAM, or SAM")
    special_needs: Optional[str] = Field(None, description="Special healthcare assistance required")

    @field_validator("age", mode="before")
    @classmethod
    def sanitize_age(cls, v: Any) -> int:
        if v is None or v == "":
            return 0
        try:
            val = int(v)
            return max(0, min(125, val))
        except (ValueError, TypeError):
            return 0

    @field_validator("full_name", mode="before")
    @classmethod
    def sanitize_name(cls, v: Any) -> str:
        s = str(v).strip() if v else ""
        return s if s else "Family Member"

# Household Registration Schema
class HouseholdRegistrationSchema(BaseModel):
    area_id: Optional[str] = Field(None, description="Assigned geographical area ID")
    head_of_family: str = Field(..., description="Full name of family head")
    address: str = Field(..., description="Complete residential address")
    pincode: str = Field(..., description="6-digit PIN code")
    village: str = Field(..., description="Village or Locality")
    contact_number: Optional[str] = Field(None, description="Primary contact number")
    house_type: str = Field("Pucca", description="Pucca, Semi-Pucca, Kutcha")
    water_source: str = Field("Piped Water / Tap", description="Primary drinking water source")
    toilet_available: str = Field("Individual Household Latrine (IHHL)", description="Toilet facility")
    sanitation_facility: str = Field("Closed Drainage", description="Drainage / sanitation type")
    survey_status: str = Field("completed", description="Survey status: 'draft' or 'completed'")
    survey_date: Optional[str] = Field(None, description="Date of survey YYYY-MM-DD")
    remarks: Optional[str] = Field(None, description="Surveyor field remarks")
    family_members: List[FamilyMemberSchema] = Field(default_factory=list, description="Family members list")

    @field_validator("head_of_family", "address", mode="before")
    @classmethod
    def ensure_non_empty(cls, v: Any) -> str:
        s = str(v).strip() if v else ""
        if not s:
            raise ValueError("Field cannot be empty")
        return s

    @field_validator("pincode", mode="before")
    @classmethod
    def sanitize_pincode(cls, v: Any) -> str:
        s = str(v).strip() if v else "571428"
        digits = "".join(filter(str.isdigit, s))
        if len(digits) == 6:
            return digits
        return s

@router.get("", response_model=List[Dict[str, Any]])
def list_households(
    pincode: Optional[str] = Query(None, description="Filter by PIN code"),
    village: Optional[str] = Query(None, description="Filter by Village"),
    area_id: Optional[str] = Query(None, description="Filter by Area ID"),
    status: Optional[str] = Query(None, description="Filter by status: pending, draft, completed"),
    search: Optional[str] = Query(None, description="Search by Household Code, Head, or Address"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Lists households with area-based access control."""
    return get_households(
        user=current_user,
        pincode=pincode,
        village=village,
        area_id=area_id,
        status=status,
        search=search,
        limit=limit,
        offset=offset
    )

@router.post("", status_code=status.HTTP_201_CREATED)
def create_household(
    household_in: HouseholdRegistrationSchema,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Registers a new household and family survey with all members and health information.
    Automatically assigns a unique household code and checks for duplicate registrations.
    """
    try:
        payload = household_in.model_dump()
        # Guarantee survey_date is populated
        if not payload.get("survey_date"):
            payload["survey_date"] = date.today().strftime("%Y-%m-%d")

        result = register_household_and_survey(payload, user=current_user)
        return result
    except DuplicateHouseholdError as dhe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(dhe)
        )
    except UnauthorizedAccessError as uae:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(uae)
        )
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register household survey: {str(e)}"
        )

@router.get("/{household_id}")
def get_household(
    household_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieves complete household profile, all family members, and health info."""
    try:
        details = get_household_details(household_id, user=current_user)
        if not details:
            raise HTTPException(status_code=404, detail=f"Household '{household_id}' not found.")
        return details
    except UnauthorizedAccessError as uae:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(uae)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch household profile: {str(e)}"
        )

@router.put("/{household_id}")
def update_household(
    household_id: str,
    update_in: HouseholdRegistrationSchema,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Updates an existing household record, family members, and survey status."""
    try:
        payload = update_in.model_dump()
        if not payload.get("survey_date"):
            payload["survey_date"] = date.today().strftime("%Y-%m-%d")

        result = update_household_and_survey(household_id, payload, user=current_user)
        return result
    except UnauthorizedAccessError as uae:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(uae)
        )
    except NotFoundError as nfe:
        raise HTTPException(status_code=404, detail=str(nfe))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update household record: {str(e)}"
        )

@router.delete("/{household_id}")
def remove_household(
    household_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes a household and all associated family members and survey records."""
    try:
        result = delete_household(household_id, user=current_user)
        return result
    except UnauthorizedAccessError as uae:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(uae)
        )
    except NotFoundError as nfe:
        raise HTTPException(status_code=404, detail=str(nfe))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete household record: {str(e)}"
        )

@router.post("/{household_id}/members", status_code=status.HTTP_201_CREATED)
def create_household_member(
    household_id: str,
    member_in: FamilyMemberSchema,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Adds a new family member to an existing household."""
    try:
        result = add_family_member(household_id, member_in.model_dump(), user=current_user)
        return result
    except UnauthorizedAccessError as uae:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(uae)
        )
    except NotFoundError as nfe:
        raise HTTPException(status_code=404, detail=str(nfe))
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add family member: {str(e)}"
        )

@router.put("/{household_id}/members/{member_id}")
def edit_household_member(
    household_id: str,
    member_id: str,
    member_in: FamilyMemberSchema,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Updates an individual family member's details."""
    try:
        result = update_family_member(household_id, member_id, member_in.model_dump(), user=current_user)
        return result
    except UnauthorizedAccessError as uae:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(uae)
        )
    except NotFoundError as nfe:
        raise HTTPException(status_code=404, detail=str(nfe))
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update family member: {str(e)}"
        )

@router.delete("/{household_id}/members/{member_id}")
def remove_household_member(
    household_id: str,
    member_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes an individual family member from a household."""
    try:
        result = delete_family_member(household_id, member_id, user=current_user)
        return result
    except UnauthorizedAccessError as uae:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(uae)
        )
    except NotFoundError as nfe:
        raise HTTPException(status_code=404, detail=str(nfe))
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete family member: {str(e)}"
        )

# Analytics Router
analytics_router = APIRouter(prefix="/api/surveys", tags=["Survey Analytics"])

@analytics_router.get("/analytics")
def get_analytics(
    pincode: Optional[str] = Query(None, description="Filter by PIN code"),
    village: Optional[str] = Query(None, description="Filter by Village"),
    worker_id: Optional[str] = Query(None, description="Filter by ASHA worker ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Returns dashboard analytics and demographic statistics."""
    try:
        return get_survey_analytics(
            user=current_user,
            pincode=pincode,
            village=village,
            worker_id=worker_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate survey analytics: {str(e)}"
        )
