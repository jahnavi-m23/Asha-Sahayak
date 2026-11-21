"""
ASHA SAHAYAK - Unified FastAPI Application.
Integrates:
- Phase 1: Real-time voice capture, streaming STT (Gnani Prisma), and TTS synthesis (Gnani Timbre)
- Phase 2: AI Understanding, Structured Data Extraction, Safety Danger-Sign Detection, Voice Readback & Correction
- Phase 3: Field visit register persistence, SQLite thread-safe storage, RBAC, and Community Health Management
"""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.voice.config import config
from backend.database.crud import init_db, seed_database_if_empty

from backend.routes import (
    voice_router,
    ai_router,
    report_router,
    visits_router,
    beneficiaries_router,
    followups_router,
    reports_router,
    auth_router,
    areas_router,
    households_router,
    analytics_router,
    workers_router,
)
from backend.routes.voice import voice_streaming_endpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("asha_sahayak.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing %s (v%s)...", settings.APP_NAME, settings.APP_VERSION)
    # Initialize SQLite database and seed synthetic demo data if needed
    try:
        init_db()
        seed_database_if_empty(force=False)
        logger.info("Phase 3 SQLite database verified and seeded.")
    except Exception as db_err:
        logger.warning("Database initialization notice: %s", db_err)

    logger.info("Loaded safety rules for danger sign detection.")
    logger.info("Ready for Phase 1 voice inputs, Phase 2 AI processing, and Phase 3 persistence.")
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


# Single shared FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Integrated AI-Powered Voice Field Register and Community Healthcare Management "
        "System for ASHA Workers and Primary Health Centres (PHCs).\n\n"
        "- Phase 1: Real-time Voice Capture, Streaming STT & TTS across 10 Indian Languages.\n"
        "- Phase 2: AI Understanding, Structured Clinical Extraction, Danger-Sign Detection & Voice Corrections.\n"
        "- Phase 3: Field Register Persistence, SQLite Database, Household Profiling & Follow-up Tracking."
    ),
    lifespan=lifespan
)

# Configure CORS for web and mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins if config.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Phase 1, Phase 2, and Phase 3 Routers without duplicates
app.include_router(voice_router)
app.include_router(ai_router)
app.include_router(report_router)
app.include_router(visits_router)
app.include_router(beneficiaries_router)
app.include_router(followups_router)
app.include_router(reports_router)
app.include_router(auth_router)
app.include_router(areas_router)
app.include_router(households_router)
app.include_router(analytics_router)
app.include_router(workers_router)


# WebSocket alias for /ws/audio connecting to voice streaming
@app.websocket("/ws/audio")
async def websocket_audio_alias(
    websocket: WebSocket,
    language: str = Query(default="indic-auto")
):
    await voice_streaming_endpoint(websocket=websocket, language=language)


@app.get("/api/meta", tags=["General"])
def api_meta():
    """Returns metadata for all three integrated phases."""
    return {
        "project": "ASHA SAHAYAK",
        "phase": "Phase 2: AI Understanding, Data Extraction and Safety",
        "phases_supported": [
            "Phase 1: Voice Input, Speech Recognition & TTS (Prisma v3.0 / Timbre v2.5)",
            "Phase 2: AI Clinical Extraction, Danger-Sign Detection & Safety Rules",
            "Phase 3: Database, Field Register, Household Surveys & Follow-up Management"
        ],
        "status": "online",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "endpoints": {
            "voice_stream": "/api/voice/stream",
            "voice_websocket_alias": "/ws/audio",
            "voice_status": "/api/voice/status",
            "voice_tts": "/api/voice/tts",
            "voice_translate": "/api/voice/translate",
            "ai_process_transcript": "/api/ai/process-transcript",
            "ai_correct_record": "/api/ai/correct-record",
            "report_extract": "/api/report/extract",
            "report_save": "/api/report/save",
            "report_list": "/api/report/list",
            "visits_confirm": "/api/visits/confirm",
            "visits_list": "/api/visits",
            "beneficiaries": "/api/beneficiaries",
            "followups": "/api/followups",
            "households": "/api/households",
            "workers_find": "/api/workers/find",
            "auth_login": "/api/auth/login"
        }
    }


@app.get("/health", tags=["General"])
def health():
    """Global service health check."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "gnani_configured": config.has_real_credentials
    }


@app.get("/api/health", tags=["General"])
def health_check():
    """Comprehensive system health check for all 3 phases."""
    return {
        "status": "healthy",
        "service": "ASHA Sahayak Integrated Platform",
        "database": "SQLite",
        "mode": "SYNTHETIC HEALTHCARE DEMO",
        "phases": {
            "phase_1": "Voice Recognition (Streaming & Speech-to-Text active)",
            "phase_2": "AI Processing (Clinical Extraction & Safety Engine active)",
            "phase_3": "Database, Dashboard, Household & Follow-up Management active"
        },
        "features": [
            "Voice Recognition (10 Indian Languages)",
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
    async def serve_spa(request: Request, full_path: str = ""):
        # Do not intercept API, docs, or WebSocket routes
        if full_path.startswith("api/") or full_path.startswith("ws/") or full_path in ("docs", "redoc", "openapi.json", "health"):
            return None
        # When hitting root directly with API/test clients that don't request text/html, return metadata
        if (full_path == "" or full_path == "/") and "text/html" not in request.headers.get("accept", ""):
            return api_meta()
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend index.html not found"}
else:
    @app.get("/", tags=["General"])
    def root_redirect():
        return api_meta()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=config.backend_host,
        port=config.backend_port,
        reload=True
    )
