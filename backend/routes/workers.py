"""
Workers API Router for ASHA Sahayak
Provides Public ASHA Worker Location Finder, Worker Personalized Dashboard,
Administrative Worker Management (Register, Reassign, Status, Password Reset),
and Health Supervisor Jurisdiction Monitoring.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field

from backend.routes.auth import get_current_user
from backend.database.crud import (
    find_asha_workers,
    get_worker_dashboard_summary,
    admin_list_workers,
    admin_register_worker,
    admin_update_worker,
    admin_reset_worker_password,
    supervisor_get_overview,
    get_audit_logs,
    NotFoundError,
    ValidationError
)

router = APIRouter(prefix="/api/workers", tags=["ASHA Workers"])

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class WorkerRegisterRequest(BaseModel):
    full_name: str = Field(..., description="ASHA worker full name e.g. 'Sunita Devi'")
    username: str = Field(..., description="Unique login identifier e.g. 'asha_rampur'")
    password: Optional[str] = Field("asha123", description="Initial password")
    badge_id: Optional[str] = Field(None, description="Official department badge ID e.g. 'ASHA-KA-MDY-001'")
    mobile: Optional[str] = Field(None, description="Mobile contact number")
    work_contact: Optional[str] = Field(None, description="Official public contact number")
    phc_name: Optional[str] = Field("Kestur Primary Health Centre", description="Associated Primary Health Centre")
    assigned_area_id: Optional[str] = Field(None, description="Geographical Area ID to assign")

class WorkerUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    badge_id: Optional[str] = None
    mobile: Optional[str] = None
    work_contact: Optional[str] = None
    phc_name: Optional[str] = None
    assigned_area_id: Optional[str] = None
    is_active: Optional[int] = None
    is_verified: Optional[int] = None

class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=4, description="New account password")

# ============================================================================
# PUBLIC ASHA WORKER FINDER (NO AUTH REQUIRED)
# ============================================================================

@router.get("/find", summary="Public location-based ASHA worker finder")
def public_find_asha_workers(
    q: Optional[str] = None,
    pincode: Optional[str] = None,
    village: Optional[str] = None,
    locality: Optional[str] = None,
    taluk: Optional[str] = None,
    district: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """
    Public lookup endpoint to find officially registered and verified ASHA workers
    for any geographical location in Karnataka.
    Never exposes sensitive private information (passwords, home address, medical data).
    """
    workers = find_asha_workers(
        query=q,
        pincode=pincode,
        village=village,
        locality=locality,
        taluk=taluk,
        district=district,
        latitude=lat,
        longitude=lon
    )

    query_summary = {
        "q": q,
        "pincode": pincode,
        "village": village,
        "locality": locality,
        "taluk": taluk,
        "district": district,
        "coordinates": {"lat": lat, "lon": lon} if (lat is not None and lon is not None) else None
    }

    if workers:
        msg = f"Found {len(workers)} verified ASHA worker(s) for your location."
    else:
        msg = (
            "No verified ASHA workers found for this location. "
            "Please contact your nearest Primary Health Centre or Taluk Health Office for assistance."
        )

    return {
        "status": "success",
        "total_found": len(workers),
        "query": query_summary,
        "message": msg,
        "workers": workers
    }

# ============================================================================
# ASHA WORKER PERSONALIZED DASHBOARD
# ============================================================================

@router.get("/my-dashboard", summary="Personalized ASHA Worker Dashboard")
def get_my_dashboard(
    worker_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Returns personalized field metrics, assigned area overview, today's schedule,
    and high-risk beneficiary alerts for the authenticated ASHA worker.
    """
    # Determine target worker ID
    target_id = current_user["id"]
    if current_user["role"] in ("admin", "health_supervisor") and worker_id:
        target_id = worker_id
    elif current_user["role"] != "asha_worker" and not worker_id:
        # Default to primary ASHA worker if admin views dashboard
        target_id = "USR-ASHA-RAMPUR"

    try:
        summary = get_worker_dashboard_summary(target_id)
        return {
            "status": "success",
            "dashboard": summary
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# ============================================================================
# ADMINISTRATOR WORKER MANAGEMENT
# ============================================================================

@router.get("/admin/list", summary="Admin listing of all ASHA workers")
def admin_get_all_workers(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists all registered ASHA workers, assigned areas, and survey performance."""
    if current_user["role"] not in ("admin", "health_supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Administrator or Supervisor role required."
        )
    workers = admin_list_workers()
    return {
        "status": "success",
        "total": len(workers),
        "workers": workers
    }

@router.post("/admin/register", status_code=status.HTTP_201_CREATED, summary="Admin registers a new ASHA worker")
def admin_create_worker(
    req: WorkerRegisterRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Creates a new ASHA worker profile, issues badge ID, and assigns geographical sector."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Only Administrators can register new ASHA workers."
        )
    try:
        new_worker = admin_register_worker(req.model_dump(), performed_by=current_user["id"])
        return {
            "status": "success",
            "message": f"Successfully registered ASHA worker {new_worker['full_name']}.",
            "worker": new_worker
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/admin/{worker_id}", summary="Admin updates ASHA worker profile or reassigns area")
def admin_edit_worker(
    worker_id: str,
    req: WorkerUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Updates worker details, activation/verification status, or reassigns service area."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Only Administrators can modify ASHA worker profiles."
        )
    try:
        updated = admin_update_worker(
            worker_id=worker_id,
            updates=req.model_dump(exclude_unset=True),
            performed_by=current_user["id"]
        )
        return {
            "status": "success",
            "message": f"Updated profile for {updated['full_name']}.",
            "worker": updated
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/admin/{worker_id}/reset-password", summary="Admin resets worker password")
def admin_reset_password(
    worker_id: str,
    req: PasswordResetRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Administrative override to reset an ASHA worker's login password."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Only Administrators can reset worker credentials."
        )
    try:
        admin_reset_worker_password(worker_id, req.new_password, performed_by=current_user["id"])
        return {
            "status": "success",
            "message": "Password successfully reset."
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# ============================================================================
# HEALTH SUPERVISOR JURISDICTION MONITORING
# ============================================================================

@router.get("/supervisor/overview", summary="Supervisor taluk jurisdiction overview")
def get_supervisor_overview(
    taluk: Optional[str] = "Maddur",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Provides taluk-wide monitoring: survey coverage, active workers,
    village-level breakdown, and highlights unassigned villages for administrative action.
    """
    if current_user["role"] not in ("admin", "health_supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Supervisor or Administrator credentials required."
        )
    overview = supervisor_get_overview(current_user["id"], taluk=taluk)
    return {
        "status": "success",
        "overview": overview
    }

@router.get("/audit-logs", summary="Administrative audit trail")
def list_audit_trail(
    limit: int = 25,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieves recent administrative and operational audit events."""
    if current_user["role"] not in ("admin", "health_supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Only Administrators and Supervisors can view audit logs."
        )
    logs = get_audit_logs(limit=limit)
    return {
        "status": "success",
        "total": len(logs),
        "audit_logs": logs
    }
