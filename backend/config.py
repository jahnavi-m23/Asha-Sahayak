# backend/config.py
"""
Configuration management for ASHA SAHAYAK Phase 2.
Loads environment variables safely with defaults and validation.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for Phase 2 AI & Safety backend."""
    
    # General App Config
    APP_NAME: str = "ASHA SAHAYAK - AI Understanding & Safety Backend"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Qwen AI Configuration
    # Supports DashScope API, OpenRouter, Together AI, or local OpenAI-compatible endpoint
    QWEN_API_KEY: Optional[str] = Field(default=None, description="API Key for Qwen LLM")
    QWEN_API_BASE: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        description="Base URL for Qwen OpenAI-compatible API"
    )
    QWEN_MODEL_NAME: str = Field(
        default="qwen-plus",
        description="Qwen model identifier (e.g. qwen-plus, qwen-turbo, qwen-2.5-72b-instruct)"
    )
    QWEN_TIMEOUT_SECONDS: float = 25.0
    
    # Gnani Timbre v3.0 TTS Configuration
    GNANI_API_KEY: Optional[str] = Field(default=None, description="API Key for Gnani Timbre TTS")
    GNANI_TOKEN: Optional[str] = Field(default=None, description="Auth token for Gnani Timbre")
    GNANI_TIMBRE_URL: str = Field(
        default="https://api.gnani.ai/timbre/v3/synthesize",
        description="Endpoint URL for Gnani Timbre v3.0 text-to-speech API"
    )
    GNANI_TIMEOUT_SECONDS: float = 15.0
    
    # Phase 3 Shared Backend Integration
    PHASE_3_ENDPOINT_URL: str = Field(
        default="http://localhost:8000/api/records/save",
        description="Endpoint URL of Phase 3 backend to receive confirmed records"
    )
    PHASE_3_API_KEY: Optional[str] = Field(default=None, description="Authentication key for Phase 3")
    
    # Public Health Safety & Protocol Settings
    DEFAULT_LANGUAGE: str = "kn-en"
    REQUIRE_EXPLICIT_CONFIRMATION: bool = True
    ALLOW_MOCK_FALLBACK: bool = True  # Allows offline/mock operations when API keys are not supplied
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
