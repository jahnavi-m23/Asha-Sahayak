"""
Reports & Analytics API Router for ASHA Sahayak Phase 3.
Provides high-level healthcare metrics, referral alerts, and vaccination tracking.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from backend.database.crud import (
    get_dashboard_reports,
    seed_database_if_empty,
)

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("", response_model=Dict[str, Any])
def get_reports():
    """
    Returns aggregated healthcare dashboard statistics:
    - Number of completed visits
    - Upcoming follow-ups
    - Pending / overdue follow-ups
    - Referral alerts
    - Vaccinations due breakdown
    """
    try:
        return get_dashboard_reports()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate reports: {str(e)}"
        )

@router.post("/reset-demo", status_code=status.HTTP_200_OK)
def reset_synthetic_demo_data():
    """
    Resets database with fresh synthetic demo data for live demonstrations.
    """
    try:
        seed_database_if_empty(force=True)
        return {
            "status": "success",
            "message": "SQLite database re-seeded with fresh synthetic demo data.",
            "reports": get_dashboard_reports()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset demo data: {str(e)}"
        )
