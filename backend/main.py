# backend/main.py
"""
ASHA SAHAYAK - Unified FastAPI Application.
Integrates:
- Phase 1: Real-time voice capture, streaming STT (Gnani Prisma), and TTS synthesis (Gnani Timbre)
- Phase 2: AI Understanding, Structured Data Extraction, Safety Danger-Sign Detection, Voice Readback & Correction
- Phase 3: Field visit register persistence and handoff
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.voice.config import config
from backend.routes.ai import router as ai_router
from backend.routes.voice import router as voice_router
from backend.routes.report import router as report_router

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
    logger.info("Ready for Phase 1 voice inputs, Phase 2 AI processing, and Phase 3 persistence.")
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


# Single shared FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered voice-based field register for ASHA workers. "
        "Phase 1: Real-time Voice Capture, Streaming STT & TTS. "
        "Phase 2: AI Understanding, Structured Data Extraction, Danger-Sign Detection & Voice Corrections. "
        "Phase 3: Beneficiary Records & Field Register Persistence."
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

# Register routers without duplicate registrations
app.include_router(voice_router)
app.include_router(report_router)
app.include_router(ai_router)


@app.get("/", tags=["General"])
async def root():
    """Root entry point providing API metadata for all phases."""
    return {
        "project": "ASHA SAHAYAK",
        "phase": "Phase 2: AI Understanding, Data Extraction and Safety",
        "phases_supported": [
            "Phase 1: Voice Input and Speech Recognition",
            "Phase 2: AI Understanding, Data Extraction and Safety",
            "Phase 3: Field Register and Dashboard"
        ],
        "status": "online",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/ai/health",
        "endpoints": {
            "voice_stream": "/api/voice/stream",
            "voice_synthesize": "/api/voice/synthesize",
            "voice_translate": "/api/voice/translate",
            "voice_languages": "/api/voice/languages",
            "voice_status": "/api/voice/status",
            "report_extract": "/api/report/extract",
            "report_save": "/api/report/save",
            "report_list": "/api/report/list",
            "process_transcript": "/api/ai/process-transcript",
            "correct_record": "/api/ai/correct-record",
            "confirm_record": "/api/ai/confirm-record",
            "synthesize_speech": "/api/ai/synthesize-speech",
            "danger_signs_rules": "/api/ai/danger-signs/rules",
            "websocket_interaction": "/api/ai/ws/interaction"
        }
    }


@app.get("/health", tags=["General"])
async def health():
    """Global service health check."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "gnani_configured": config.has_real_credentials
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=config.backend_host,
        port=config.backend_port,
        reload=True
    )
