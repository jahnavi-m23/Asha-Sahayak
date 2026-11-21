# backend/main.py
"""
ASHA SAHAYAK - Shared FastAPI Application.
Hosts Phase 2 AI Understanding, Structured Data Extraction, Safety Danger-Sign Detection,
Gnani Timbre Voice Readback, Voice Correction, and Phase 3 Handoff.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.routes.ai import router as ai_router

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
    logger.info("Loaded safety rules for danger sign detection.")
    logger.info("Ready for Phase 1 transcript inputs and Phase 3 persistence handoffs.")
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


# Shared FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered voice-based field register for ASHA workers. "
        "Phase 2 provides transcript understanding, structured entity extraction, "
        "danger-sign detection with clinical guidelines, Gnani Timbre voice read-back, "
        "and explicit confirmation loops."
    ),
    lifespan=lifespan
)

# CORS Middleware for web/mobile client interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Phase 2 AI & Safety router
app.include_router(ai_router)


@app.get("/", tags=["General"])
async def root():
    """Root entry point providing API metadata."""
    return {
        "project": "ASHA SAHAYAK",
        "phase": "Phase 2: AI Understanding, Data Extraction and Safety",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/ai/health",
        "endpoints": {
            "process_transcript": "/api/ai/process-transcript",
            "correct_record": "/api/ai/correct-record",
            "confirm_record": "/api/ai/confirm-record",
            "synthesize_speech": "/api/ai/synthesize-speech",
            "danger_signs_rules": "/api/ai/danger-signs/rules",
            "websocket_interaction": "/ws/ai/interaction"
        }
    }


@app.get("/health", tags=["General"])
async def health():
    """Global service health check."""
    return {"status": "ok", "app": settings.APP_NAME}
