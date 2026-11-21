# backend/ai/voice_readback.py
"""
Gnani Timbre v3.0 Text-to-Speech Integration.
Reads back extracted medical details, missing field prompts, and danger signs to the ASHA worker.
Handles:
- Kannada (kn-IN) and Indian English (en-IN).
- Calling Gnani Timbre v3.0 API with backend auth tokens.
- Safe offline fallback mock synthesizing valid WAV audio bytes for testing.
"""
import base64
import logging
import struct
from typing import Optional
import httpx

from backend.config import settings
from backend.models.schemas import VoiceReadbackResponse, SupportedLanguage

logger = logging.getLogger("asha_sahayak.ai.voice_readback")


class VoiceReadbackService:
    """Manages voice synthesis using Gnani Timbre v3.0."""

    def __init__(self):
        self.api_url = settings.GNANI_TIMBRE_URL
        self.api_key = settings.GNANI_API_KEY
        self.token = settings.GNANI_TOKEN

    async def synthesize_speech(
        self,
        text: str,
        language: str = "kn-en"
    ) -> VoiceReadbackResponse:
        """
        Synthesize text into speech via Gnani Timbre v3.0.
        Falls back to safe mock audio when offline or without API key.
        """
        if not text or not text.strip():
            text = "No details to read back."

        gnani_lang = self._map_language_code(language)

        # If live credentials exist, call Gnani API; fall back to mock only if API call fails or no keys
        if self.api_key or self.token:
            try:
                return await self._call_gnani_api(text, gnani_lang)
            except Exception as e:
                if settings.ALLOW_MOCK_FALLBACK:
                    logger.warning("Gnani Timbre API call failed (%s); using fallback mock audio", str(e))
                    return self._generate_mock_audio_response(text, gnani_lang)
                else:
                    raise
        elif settings.ALLOW_MOCK_FALLBACK:
            return self._generate_mock_audio_response(text, gnani_lang)
        else:
            raise ValueError("GNANI_API_KEY/TOKEN is not configured and ALLOW_MOCK_FALLBACK is False")

    async def _call_gnani_api(self, text: str, gnani_lang: str) -> VoiceReadbackResponse:
        """Call live Gnani Timbre v3.0 endpoint."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token or self.api_key}",
            "x-api-key": self.api_key or ""
        }
        payload = {
            "text": text,
            "language": gnani_lang,
            "audio_format": "wav",
            "speed": 1.0,
            "sample_rate": 16000
        }

        async with httpx.AsyncClient(timeout=settings.GNANI_TIMEOUT_SECONDS) as client:
            resp = await client.post(self.api_url, headers=headers, json=payload)
            resp.raise_for_status()
            
            # Check response format (can be JSON with base64 audio or raw audio stream)
            content_type = resp.headers.get("content-type", "")
            if "json" in content_type:
                res_data = resp.json()
                b64_audio = res_data.get("audio_content") or res_data.get("data")
            else:
                b64_audio = base64.b64encode(resp.content).decode("utf-8")

            return VoiceReadbackResponse(
                readback_text=text,
                language=gnani_lang,
                audio_base64=b64_audio,
                audio_format="wav",
                is_mock=False
            )

    def _map_language_code(self, lang: str) -> str:
        """Normalize language to Gnani Timbre v3.0 format."""
        lang_lower = lang.lower()
        if "kn" in lang_lower:
            return "kn-IN"
        return "en-IN"

    def _generate_mock_audio_response(self, text: str, language: str) -> VoiceReadbackResponse:
        """Generate a valid, compact synthetic WAV header for reliable testing."""
        # 16000 Hz, 16-bit, mono PCM silence/tone header
        sample_rate = 16000
        num_samples = 1600  # 0.1 second of audio
        byte_rate = sample_rate * 2
        block_align = 2
        data_size = num_samples * 2

        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + data_size,
            b'WAVE',
            b'fmt ',
            16,
            1,  # PCM
            1,  # Mono
            sample_rate,
            byte_rate,
            block_align,
            16, # Bits per sample
            b'data',
            data_size
        )
        audio_bytes = wav_header + (b'\x00' * data_size)
        b64_str = base64.b64encode(audio_bytes).decode('ascii')

        return VoiceReadbackResponse(
            readback_text=text,
            language=language,
            audio_base64=b64_str,
            audio_format="wav",
            is_mock=True
        )
