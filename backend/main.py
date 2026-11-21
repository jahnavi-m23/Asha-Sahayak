import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.voice.config import config
from backend.routes.voice import router as voice_router
from backend.routes.report import router as report_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

app = FastAPI(
    title="ASHA Sahayak – AI Field Register Backend",
    description="ASHA Sahayak Backend Services. Phase 1: Voice Input, Phase 2: Extraction, Phase 3: Field Register.",
    version="2.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins if config.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Voice & Report routers
app.include_router(voice_router)
app.include_router(report_router)

@app.get("/")
async def root():
    return {
        "project": "ASHA SAHAYAK",
        "phase": "Phase 1: Voice Input and Speech Recognition",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
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

