from .visits import router as visits_router
from .beneficiaries import router as beneficiaries_router
from .followups import router as followups_router
from .reports import router as reports_router
from .auth import router as auth_router
from .areas import router as areas_router
from .households import router as households_router, analytics_router
from .workers import router as workers_router
from .voice import router as voice_router

__all__ = [
    "visits_router",
    "beneficiaries_router",
    "followups_router",
    "reports_router",
    "auth_router",
    "areas_router",
    "households_router",
    "analytics_router",
    "workers_router",
    "voice_router",
]
