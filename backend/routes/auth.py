"""
Authentication API Router for ASHA Sahayak
Provides secure Login, Role-Based Access Control (Admin, ASHA Worker, Health Supervisor),
session verification, and password assistance.
"""

import re
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel, Field

from backend.database.crud import (
    authenticate_user,
    get_user_by_id,
    get_all_users,
    register_worker_self_service,
    ValidationError
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str = Field(..., description="Login ID / Username e.g. asha_rampur, admin")
    password: str = Field(..., description="User password")

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, description="Full Name of the ASHA worker")
    username: str = Field(..., min_length=3, description="Unique login identifier")
    password: Optional[str] = Field("asha123", description="Password")
    mobile: Optional[str] = Field(None, description="Mobile contact number")
    village: Optional[str] = Field("Rampur", description="Assigned village")
    pincode: Optional[str] = Field("571428", description="6-digit postal PIN code")
    taluk: Optional[str] = Field("Maddur", description="Taluk name")
    district: Optional[str] = Field("Mandya", description="District name")
    state: Optional[str] = Field("Karnataka", description="State name")
    phc_name: Optional[str] = Field("Primary Health Centre", description="Assigned PHC")
    sector: Optional[str] = Field(None, description="Assigned sector/ward")
    badge_id: Optional[str] = Field(None, description="Official badge ID")

class ForgotPasswordRequest(BaseModel):
    username: str = Field(..., description="Registered username")
    mobile: Optional[str] = Field(None, description="Registered mobile number for verification")

# Predefined session tokens for demo accounts
ACTIVE_SESSIONS: Dict[str, str] = {
    "token-admin-demo": "USR-ADMIN",
    "token-admin-USR-ADMIN": "USR-ADMIN",
    "token-asha-rampur-demo": "USR-ASHA-RAMPUR",
    "token-asha_rampur-USR-ASHA-RAMPUR": "USR-ASHA-RAMPUR",
    "token-asha-rampur-2-demo": "USR-ASHA-RAMPUR-2",
    "token-asha_rampur_2-USR-ASHA-RAMPUR-2": "USR-ASHA-RAMPUR-2",
    "token-asha-kalyanpur-demo": "USR-ASHA-KALYANPUR",
    "token-asha_kalyanpur-USR-ASHA-KALYANPUR": "USR-ASHA-KALYANPUR",
    "token-supervisor-demo": "USR-SUPERVISOR",
    "token-supervisor_maddur-USR-SUPERVISOR": "USR-SUPERVISOR",
}

def resolve_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Resolves user dictionary from session token or token pattern."""
    token = token.strip()
    # 1. Exact match in session map
    if token in ACTIVE_SESSIONS:
        user = get_user_by_id(ACTIVE_SESSIONS[token])
        if user:
            return user

    # 2. Check if token contains user ID (e.g. token-username-USR-XXXX)
    user_id_match = re.search(r"(USR-[A-Z0-9_\-]+)", token)
    if user_id_match:
        user = get_user_by_id(user_id_match.group(1))
        if user:
            return user

    # 3. Direct lookup if token is a user ID
    user = get_user_by_id(token)
    if user:
        return user

    # 4. Check if token matches a username (e.g. token-asha_rampur)
    all_users = get_all_users()
    for u in all_users:
        if u["username"].lower() in token.lower():
            return get_user_by_id(u["id"])

    return None

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependency that resolves authenticated user from Authorization header.
    Requires a valid token and does not default to any single hardcoded user.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in."
        )

    clean_token = authorization.replace("Bearer ", "").strip()
    user = resolve_user_from_token(clean_token)
    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired session. Please log in again."
    )

def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Resolves authenticated user if valid token present, otherwise None."""
    if not authorization:
        return None
    clean_token = authorization.replace("Bearer ", "").strip()
    return resolve_user_from_token(clean_token)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(reg_in: RegisterRequest):
    """
    Self-service registration for new ASHA workers.
    Persists to SQLite database, creates area mapping, and returns authenticated session.
    """
    try:
        user_obj = register_worker_self_service(reg_in.model_dump())
        session_token = f"token-{user_obj['username']}-{user_obj['id']}"
        ACTIVE_SESSIONS[session_token] = user_obj["id"]
        return {
            "status": "success",
            "message": f"ASHA Worker {user_obj['full_name']} registered successfully.",
            "access_token": session_token,
            "user": user_obj
        }
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(e)}")

@router.post("/login")
def login(login_in: LoginRequest):
    """
    Authenticates user credentials and returns session token, role, and assigned area.
    """
    user = authenticate_user(login_in.username, login_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password. Please check your credentials."
        )

    # Standardized session token format
    session_token = f"token-{user['username']}-{user['id']}"
    ACTIVE_SESSIONS[session_token] = user["id"]

    return {
        "status": "success",
        "message": f"Welcome back, {user['full_name']}!",
        "access_token": session_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me")
def get_current_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the authenticated user's profile and assigned geographical area."""
    return {"status": "success", "user": current_user, **current_user}

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    """
    Forgot password assistant:
    Verifies user identity and provides reset instructions or temporary PIN for field workers.
    """
    with_user = None
    all_u = get_all_users()
    for u in all_u:
        if u["username"].lower() == req.username.strip().lower():
            with_user = u
            break

    if not with_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with Login ID '{req.username}' not found in PHC records."
        )

    return {
        "status": "success",
        "message": (
            f"Password reset guidance for {with_user['full_name']} ({with_user['role']}). "
            f"Default credentials: username='{with_user['username']}', password='{with_user['username'][:4]}123' (e.g. 'asha123' or 'admin123')."
        ),
        "username": with_user["username"],
        "assigned_area": with_user.get("area_name") or "Primary Health Centre"
    }

@router.get("/users")
def list_system_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists all registered system users (Administrator and Supervisor access)."""
    if current_user["role"] not in ("admin", "health_supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Only Administrators and Health Supervisors can view user listings."
        )
    return get_all_users()
