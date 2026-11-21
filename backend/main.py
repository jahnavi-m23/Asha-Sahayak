"""
ASHA Sahayak - Shared FastAPI Application
Integrated Platform:
- Phase 1: Voice Recognition (Audio Streaming & Transcription)
- Phase 2: AI Processing (Clinical Extraction Review Interface)
- Phase 3: Database, Dashboard, Follow-up & Community Health Registers
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

# Load environment variables safely
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database.crud import init_db, seed_database_if_empty
from backend.routes import (
    visits_router,
    beneficiaries_router,
    followups_router,
    reports_router,
    auth_router,
    areas_router,
    households_router,
    analytics_router,
    workers_router,
    voice_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and seed complete synthetic demo data
    init_db()
    seed_database_if_empty(force=False)
    yield

app = FastAPI(
    title="ASHA Sahayak API",
    description=(
        "Integrated AI-Powered Voice Field Register and Community Healthcare Management "
        "System for ASHA Workers and Primary Health Centres (PHCs). "
        "Combines Phase 1 Voice Streaming, Phase 2 AI Extraction Interface, and "
        "Phase 3 Database Persistence, RBAC, Household Profiling, and Follow-up Management."
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

# Mount API & WebSocket Routers
app.include_router(voice_router)
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
        "service": "ASHA Sahayak Integrated Platform",
        "database": "SQLite",
        "mode": "SYNTHETIC HEALTHCARE DEMO",
        "phases": {
            "phase_1": "Voice Recognition (Streaming & Speech-to-Text active)",
            "phase_2": "AI Processing (Contract POST /api/visits/confirm ready)",
            "phase_3": "Database, Dashboard, Household & Follow-up Management active"
        },
        "features": [
            "Voice Recognition (Kannada, Hindi, English)",
            "Worker-Confirmed Visit Persistence",
            "SHA-256 Duplicate Prevention",
            "Safe Follow-up Scheduling (No Date Fabrication)",
            "PHC Emergency Referral & Danger Signs Retention",
            "Multi-Role Access Control (Admin, ASHA Worker, Health Supervisor)",
            "Geographical Area & PIN Code Scoping",
            "Household & Family Health Profiling",
            "Public ASHA Worker Finder Portal",
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
        # Do not intercept API or WebSocket routes
        if full_path.startswith("api/") or full_path.startswith("ws/"):
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
