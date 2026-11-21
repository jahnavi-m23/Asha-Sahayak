
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent
_backend_env = _backend_dir / ".env"
_root_env = _backend_dir.parent / ".env"

try:
    from dotenv import load_dotenv
    if _backend_env.is_file():
        load_dotenv(dotenv_path=_backend_env)
    elif _root_env.is_file():
        load_dotenv(dotenv_path=_root_env)
    else:
        load_dotenv()
except ImportError:
    pass

# The 10 Indian Languages documented and supported by Gnani AI
# Voices updated to verified, tested voices available on Gnani Timbre v2.5 model
# IndicTrans2 FLORES-233 codes mapped for state-of-the-art multilingual Indic translation
SUPPORTED_LANGUAGES: Dict[str, Dict[str, Any]] = {
    "hi-IN": {
        "code": "hi-IN",
        "phase2_code": "hi",
        "indictrans2_code": "hin_Deva",
        "name": "Hindi",
        "native_name": "हिन्दी",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Nalini",
        "available_voices": ["Nalini", "Deepak"]
    },
    "kn-IN": {
        "code": "kn-IN",
        "phase2_code": "kn",
        "indictrans2_code": "kan_Knda",
        "name": "Kannada",
        "native_name": "ಕನ್ನಡ",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Devika",
        "available_voices": ["Devika", "Nayana", "Girish", "Pranav"]
    },
    "en-IN": {
        "code": "en-IN",
        "phase2_code": "en",
        "indictrans2_code": "eng_Latn",
        "name": "Indian English",
        "native_name": "English (India)",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Kaveri",
        "available_voices": ["Kaveri", "Pranav"]
    },
    "ta-IN": {
        "code": "ta-IN",
        "phase2_code": "ta",
        "indictrans2_code": "tam_Taml",
        "name": "Tamil",
        "native_name": "தமிழ்",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Oviya",
        "available_voices": ["Oviya", "Kavin"]
    },
    "te-IN": {
        "code": "te-IN",
        "phase2_code": "te",
        "indictrans2_code": "tel_Telu",
        "name": "Telugu",
        "native_name": "తెలుగు",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Devika",
        "available_voices": ["Devika", "Chitra", "Pranav"]
    },
    "ml-IN": {
        "code": "ml-IN",
        "phase2_code": "ml",
        "indictrans2_code": "mal_Mlym",
        "name": "Malayalam",
        "native_name": "മലയാളം",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Devika",
        "available_voices": ["Devika", "Radhika"]
    },
    "mr-IN": {
        "code": "mr-IN",
        "phase2_code": "mr",
        "indictrans2_code": "mar_Deva",
        "name": "Marathi",
        "native_name": "मराठी",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Madhuri",
        "available_voices": ["Madhuri", "Radhika", "Omkar"]
    },
    "bn-IN": {
        "code": "bn-IN",
        "phase2_code": "bn",
        "indictrans2_code": "ben_Beng",
        "name": "Bengali",
        "native_name": "বাংলা",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Eishani",
        "available_voices": ["Eishani", "Tanvi"]
    },
    "gu-IN": {
        "code": "gu-IN",
        "phase2_code": "gu",
        "indictrans2_code": "guj_Gujr",
        "name": "Gujarati",
        "native_name": "ગુજરાતી",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Falguni",
        "available_voices": ["Falguni", "Chirag"]
    },
    "pa-IN": {
        "code": "pa-IN",
        "phase2_code": "pa",
        "indictrans2_code": "pan_Guru",
        "name": "Punjabi",
        "native_name": "ਪੰਜਾਬੀ",
        "stt_supported": True,
        "tts_supported": True,
        "default_voice": "Kartik",
        "available_voices": ["Kartik", "Devika"]
    }
}

# Legacy voice names from older Timbre versions mapped to supported Timbre v2.5 voices
LEGACY_VOICE_ALIASES: Dict[str, str] = {
    "kavya": "Devika",
    "amala": "Oviya",
    "swathi": "Devika",
    "anitha": "Devika",
    "shubhra": "Madhuri",
    "subhra": "Madhuri",
    "mithila": "Eishani",
    "kinjal": "Falguni",
    "simran": "Kartik",
}

# Special Multi-Language & Auto-Detect options for STT
SPECIAL_STT_MODES = {
    "indic-auto": {
        "code": "indic-auto",
        "phase2_code": "auto",
        "name": "Auto-Detect (Indic Auto)",
        "native_name": "ಸ್ವಯಂಚಾಲಿತ / ಸ್ವಯಂ ಗುರುತಿಸುವಿಕೆ",
        "description": "Gnani Prisma v3.0 Automatic Language Detection across all 10 Indian languages"
    },
    "kn-IN,en-IN": {
        "code": "kn-IN,en-IN",
        "phase2_code": "kn-en",
        "name": "Kannada + English Code-Mixed",
        "native_name": "ಕನ್ನಡ + ಇಂಗ್ಲಿಷ್ (ಮಿಶ್ರ)",
        "description": "Code-mixing between Kannada and English"
    },
    "hi-IN,en-IN": {
        "code": "hi-IN,en-IN",
        "phase2_code": "hi-en",
        "name": "Hindi + English Code-Mixed",
        "native_name": "हिन्दी + English (हिंग्लिश)",
        "description": "Code-mixing between Hindi and English"
    }
}


class VoiceConfig(BaseModel):
    # Gnani Credentials
    gnani_api_key: str = os.getenv("GNANI_API_KEY", "")

    # STT: Gnani Prisma v3.0
    gnani_websocket_url: str = os.getenv("GNANI_WEBSOCKET_URL", "wss://api.vachana.ai/stt/v3/stream")
    gnani_model: str = os.getenv("GNANI_MODEL", "prisma-v3.0")
    default_language: str = os.getenv("GNANI_DEFAULT_LANGUAGE", "indic-auto")

    # TTS: Gnani Timbre v2.5
    gnani_tts_url: str = os.getenv("GNANI_TTS_URL", "https://api.vachana.ai/api/v1/tts/inference")
    gnani_tts_model: str = os.getenv("GNANI_TTS_MODEL", "timbre-v2.5")
    gnani_tts_default_voice: str = os.getenv("GNANI_TTS_DEFAULT_VOICE", "Devika")
    gnani_tts_default_language: str = os.getenv("GNANI_TTS_DEFAULT_LANGUAGE", "kn-IN")

    # Translation: AI4Bharat IndicTrans2 & Bhashini NMT
    indictrans2_endpoint: Optional[str] = os.getenv("INDICTRANS2_ENDPOINT", None)
    bhashini_endpoint: Optional[str] = os.getenv("BHASHINI_ENDPOINT", None)
    bhashini_api_key: Optional[str] = os.getenv("BHASHINI_API_KEY", None)
    bhashini_user_id: Optional[str] = os.getenv("BHASHINI_USER_ID", None)

    # Audio specifications matching Gnani Prisma v3.0 standard
    sample_rate: int = 16000  # 16 kHz
    bit_depth: int = 16       # 16-bit signed PCM
    channels: int = 1         # Mono
    chunk_size: int = 1024    # 512 samples at 16-bit PCM = 1024 bytes (32 ms)

    # Silence and speech detection thresholds (RMS calibrated for mic noise rejection)
    rms_silence_threshold: float = 200.0

    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    cors_origins: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]

    @property
    def has_real_credentials(self) -> bool:
        """Checks if a valid, non-placeholder Gnani API key is configured."""
        key = self.gnani_api_key.strip()
        if not key:
            return False
        if key in ("your_gnani_api_key_here", "YOUR_API_KEY", "placeholder", "test"):
            return False
        return len(key) >= 8

    @staticmethod
    def get_voice_for_language(lang_code: str) -> str:
        """Returns the default Timbre v2.5 voice for a given language code."""
        info = SUPPORTED_LANGUAGES.get(lang_code)
        if info:
            return info["default_voice"]
        return "Nalini"

config = VoiceConfig()
