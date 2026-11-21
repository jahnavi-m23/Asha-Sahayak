"""
ASHA Sahayak - Shared FastAPI Application
Enhanced with Login System, Role-Based Access Control, Area Scoping,
Family & Household Surveys, Health Profiling, and Phase 2/3 Registers.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database.crud import init_db, seed_database_if_empty
from backend.routes.visits import router as visits_router
from backend.routes.beneficiaries import router as beneficiaries_router
from backend.routes.followups import router as followups_router
from backend.routes.reports import router as reports_router
from backend.routes.auth import router as auth_router
from backend.routes.areas import router as areas_router
from backend.routes.households import router as households_router, analytics_router
from backend.routes.workers import router as workers_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and seed complete synthetic demo data
    init_db()
    seed_database_if_empty(force=False)
    yield

app = FastAPI(
    title="ASHA Sahayak API",
    description=(
        "Healthcare management and voice-based field register backend for ASHA workers. "
        "Includes Login & RBAC, Area & Pincode Scoping, Household Family Surveys, "
        "Member Health Profiling, and Confirmed Visit Tracking."
    ),
    version="3.5.0",
    lifespan=lifespan
)

# Enable CORS for React frontend (Vite port 5173, CRA port 3000, and local preview)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router)
app.include_router(areas_router)
app.include_router(workers_router)
app.include_router(households_router)
app.include_router(analytics_router)
app.include_router(visits_router)
app.include_router(beneficiaries_router)
app.include_router(followups_router)
app.include_router(reports_router)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "ASHA Sahayak Enhanced API",
        "database": "SQLite",
        "mode": "SYNTHETIC DEMO",
        "features": [
            "RBAC Login System",
            "Area & Pincode Scoping",
            "Family & Household Survey",
            "Individual Health Profiling",
            "Phase 2/3 Visit Registers",
            "Bilingual Interface Support"
        ]
    }

# Check if frontend/dist exists to optionally serve static production build
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Do not intercept API routes
        if full_path.startswith("api/"):
            return None
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend index.html not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
