"""API Routes package for ASHA Sahayak."""
from .ai import router as ai_router
from .voice import router as voice_router
from .report import router as report_router

__all__ = ["ai_router", "voice_router", "report_router"]
