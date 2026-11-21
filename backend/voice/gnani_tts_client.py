import io
import math
import wave
import struct
import logging
from typing import Tuple, Dict, Any, Optional
import httpx

from backend.voice.config import config, SUPPORTED_LANGUAGES, LEGACY_VOICE_ALIASES

logger = logging.getLogger("voice.gnani_tts_client")


def wrap_pcm_in_wav(pcm_bytes: bytes, sample_rate: int = 22050, channels: int = 1, width: int = 2) -> bytes:
    """Wraps raw linear PCM bytes in a standard RIFF/WAVE header for HTML5 playback."""
    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return out.getvalue()


class GnaniTimbreTTSClient:
    """
    Client for Gnani Timbre v2.5 Text-to-Speech API.
    Official Endpoint: https://api.vachana.ai/api/v1/tts/inference
    Supported Languages: 10 Indian Languages (hi-IN, kn-IN, en-IN, ta-IN, te-IN, ml-IN, mr-IN, bn-IN, gu-IN, pa-IN)
    """

    def __init__(self):
        self.api_key = config.gnani_api_key.strip()
        self.endpoint_url = config.gnani_tts_url.strip()
        self.model = config.gnani_tts_model  # "timbre-v2.5"

    def validate_language(self, language_code: str) -> str:
        """Ensures the language code is one of the 10 documented languages."""
        lang = language_code.strip()
        if lang in SUPPORTED_LANGUAGES:
            return lang
        # Fallback to default if unrecognized
        logger.warning(f"Language '{language_code}' not in supported 10 Indian languages. Defaulting to kn-IN.")
        return config.gnani_tts_default_language

    def resolve_voice(self, requested_voice: Optional[str], language_code: str) -> Tuple[str, Optional[str]]:
        """
        Resolves the voice identifier for Timbre v2.5:
        - If voice is in LEGACY_VOICE_ALIASES (e.g. 'Kavya' -> 'Devika'), resolves it cleanly.
        - If voice is already supported, uses it directly.
        - If voice is empty, uses the language default.
        Returns: (resolved_voice, note)
        """
        lang_info = SUPPORTED_LANGUAGES.get(language_code, {})
        default_voice = lang_info.get("default_voice", "Devika")
        available = lang_info.get("available_voices", [default_voice])

        if not requested_voice:
            return default_voice, None

        clean_v = requested_voice.strip()
        # Direct match in available voices
        for v in available:
            if v.lower() == clean_v.lower():
                return v, None

        # Check legacy aliases
        if clean_v.lower() in LEGACY_VOICE_ALIASES:
            resolved = LEGACY_VOICE_ALIASES[clean_v.lower()]
            note = f"Voice '{clean_v}' is mapped to supported Timbre v2.5 voice '{resolved}'."
            logger.info(note)
            return resolved, note

        # Unknown voice: check if it exists in available, otherwise return default with warning
        logger.warning(
            f"Voice '{clean_v}' may not be supported by Timbre v2.5 for {language_code}. "
            f"Defaulting to '{default_voice}'."
        )
        return default_voice, f"Voice '{clean_v}' not recognized for {language_code}. Using '{default_voice}'."

    def get_headers(self) -> Dict[str, str]:
        return {
            "X-API-Key-ID": self.api_key,
            "Content-Type": "application/json"
        }

    async def synthesize(
        self,
        text: str,
        language_code: Optional[str] = None,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> Tuple[bytes, bool, str]:
        """
        Synthesizes text into speech using Gnani Timbre v2.5.
        Returns: (audio_bytes, is_mock, engine_name)
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("TTS text cannot be empty.")

        target_lang = self.validate_language(language_code or config.gnani_tts_default_language)
        target_voice, resolution_note = self.resolve_voice(voice, target_lang)

        # 1. If real credentials exist, call Gnani Timbre v2.5
        if config.has_real_credentials:
            payload = {
                "text": clean_text,
                "voice": target_voice,
                "model": self.model,
                "language": target_lang,
                "speed": float(speed),
                "audio_config": {
                    "encoding": "linear_pcm",
                    "container": "wav",
                    "num_channels": 1,
                    "sample_rate": 22050,
                    "sample_width": 2
                }
            }

            headers = self.get_headers()
            logger.info(f"Calling Gnani Timbre v2.5 TTS ({target_lang}, voice={target_voice}) at {self.endpoint_url}")

            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(self.endpoint_url, json=payload, headers=headers)
                
                if response.status_code == 200 and len(response.content) > 100:
                    raw_audio = response.content
                    # Ensure audio has standard playable RIFF header
                    if raw_audio[:4] != b"RIFF":
                        logger.info("Adding WAV container header to raw PCM from Timbre.")
                        raw_audio = wrap_pcm_in_wav(raw_audio, sample_rate=22050)

                    logger.info(f"Gnani Timbre v2.5 synthesis successful ({len(raw_audio)} bytes)")
                    return raw_audio, False, "gnani_timbre_v2.5"
                else:
                    err_msg = f"Gnani Timbre error (HTTP {response.status_code}): {response.text}"
                    logger.error(err_msg)
                    raise RuntimeError(err_msg)

        # 2. Mock Fallback: ONLY when credentials are completely absent in dev
        logger.warning("Running TTS in developer SIMULATION mode (GNANI_API_KEY absent).")
        mock_wav = self.generate_mock_wav_chime(clean_text, target_lang)
        return mock_wav, True, "mock_fallback"

    @staticmethod
    def generate_mock_wav_chime(text: str, language_code: str) -> bytes:
        """
        Generates a valid, playable 16-bit PCM WAV audio file containing
        a gentle confirmation tone sequence so that browser audio playback works
        seamlessly during development when real Gnani credentials are absent.
        """
        sample_rate = 16000
        duration_s = 0.8
        total_samples = int(sample_rate * duration_s)

        # Harmonic chime chord (A4 440Hz and E5 659Hz)
        freq1 = 440.0
        freq2 = 659.25

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)        # Mono
            wav_file.setsampwidth(2)        # 16-bit
            wav_file.setframerate(sample_rate)

            samples = []
            for i in range(total_samples):
                t = float(i) / sample_rate
                # Exponential decay envelope
                envelope = math.exp(-3.5 * t)
                val1 = math.sin(2.0 * math.pi * freq1 * t)
                val2 = math.sin(2.0 * math.pi * freq2 * t)
                mixed = (val1 * 0.6 + val2 * 0.4) * envelope
                # Scale to signed 16-bit integer
                sample_val = int(mixed * 24000)
                sample_val = max(-32767, min(32767, sample_val))
                samples.append(sample_val)

            raw_bytes = struct.pack(f"<{len(samples)}h", *samples)
            wav_file.writeframes(raw_bytes)

        return buffer.getvalue()

