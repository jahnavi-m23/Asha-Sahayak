import json
import struct
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock

import pytest
from backend.voice.config import config, VoiceConfig, SUPPORTED_LANGUAGES, SPECIAL_STT_MODES
from backend.voice.audio_processor import AudioProcessor
from backend.voice.mock_engine import MockTranscriptionEngine
from backend.voice.gnani_client import GnaniPrismaClient
from backend.voice.gnani_tts_client import GnaniTimbreTTSClient
from backend.routes.voice import (
    get_voice_status,
    synthesize_speech,
    send_to_phase2,
    get_recent_transcripts,
    voice_streaming_endpoint,
    Phase2TranscriptPayload,
    TTSRequestPayload
)

def generate_dummy_pcm(duration_ms: int = 100, sample_rate: int = 16000, amplitude: int = 2000) -> bytes:
    """Helper to generate dummy 16-bit PCM audio samples."""
    num_samples = int(sample_rate * (duration_ms / 1000.0))
    samples = [amplitude if i % 2 == 0 else -amplitude for i in range(num_samples)]
    return struct.pack(f"<{num_samples}h", *samples)


def test_all_10_indian_languages_supported():
    """Verifies that all 10 Indian languages documented by Gnani are registered."""
    expected_10 = ["hi-IN", "kn-IN", "en-IN", "ta-IN", "te-IN", "ml-IN", "mr-IN", "bn-IN", "gu-IN", "pa-IN"]
    for lang in expected_10:
        assert lang in SUPPORTED_LANGUAGES, f"Missing language {lang} in SUPPORTED_LANGUAGES"
        info = SUPPORTED_LANGUAGES[lang]
        assert info["stt_supported"] is True
        assert info["tts_supported"] is True
        assert info["default_voice"] is not None
        assert len(info["available_voices"]) >= 1


def test_phase2_language_mapping_for_all_10():
    """Verifies mapping of all 10 languages and special modes to Phase 2 contract."""
    assert AudioProcessor.map_language_to_phase2("hi-IN") == "hi"
    assert AudioProcessor.map_language_to_phase2("kn-IN") == "kn"
    assert AudioProcessor.map_language_to_phase2("en-IN") == "en"
    assert AudioProcessor.map_language_to_phase2("ta-IN") == "ta"
    assert AudioProcessor.map_language_to_phase2("te-IN") == "te"
    assert AudioProcessor.map_language_to_phase2("ml-IN") == "ml"
    assert AudioProcessor.map_language_to_phase2("mr-IN") == "mr"
    assert AudioProcessor.map_language_to_phase2("bn-IN") == "bn"
    assert AudioProcessor.map_language_to_phase2("gu-IN") == "gu"
    assert AudioProcessor.map_language_to_phase2("pa-IN") == "pa"

    # Code-mixing and auto-detection
    assert AudioProcessor.map_language_to_phase2("kn-IN,en-IN") == "kn-en"
    assert AudioProcessor.map_language_to_phase2("hi-IN,en-IN") == "hi-en"
    assert AudioProcessor.map_language_to_phase2("indic-auto") == "auto"


def test_audio_processor_pcm_validation():
    processor = AudioProcessor(sample_rate=16000, silence_threshold=100.0)
    valid_pcm = generate_dummy_pcm(50, amplitude=1500)
    is_valid, rms, metrics = processor.process_pcm_chunk(valid_pcm)
    assert is_valid is True
    assert rms > 0.0
    assert metrics["is_speech"] is True

    invalid_pcm = b"\x01\x02\x03"
    is_valid, rms, metrics = processor.process_pcm_chunk(invalid_pcm)
    assert is_valid is False
    assert "error" in metrics


def test_mock_engine_explicitly_labeled():
    """
    Verifies that the fallback engine returns empty transcript on silence,
    and brands output with [SIMULATION] when speech occurs.
    """
    engine = MockTranscriptionEngine(language_code="indic-auto")
    
    # 1. On silence (no speech registered):
    final_silent = engine.get_final_payload()
    assert final_silent["transcript"] == ""
    assert final_silent["is_mock"] is True
    assert final_silent["speech_detected"] is False

    # 2. When speech is registered:
    engine.register_audio_chunk(1024, is_speech=True)
    engine.register_audio_chunk(1024, is_speech=True)
    assert engine.has_detected_speech() is True

    final_speech = engine.get_final_payload()
    assert final_speech["is_mock"] is True
    assert final_speech["is_simulation"] is True
    assert final_speech["engine"] == "mock_simulation"
    assert "[SIMULATION]" in final_speech["transcript"]


def test_gnani_client_headers_indic_auto():
    """Verifies STT client headers with automatic language detection."""
    client = GnaniPrismaClient(language_code="indic-auto")
    headers = client.get_connection_headers()
    assert headers["model"] == "prisma-v3.0"
    assert headers["language_code"] == "indic-auto"
    assert headers["format"] == "transcribe"
    assert "X-API-Key-ID" in headers


def test_gnani_tts_client_synthesis():
    """Verifies Gnani Timbre v2.5 TTS synthesis & WAV validation."""
    tts = GnaniTimbreTTSClient()
    audio_bytes, is_mock, engine = asyncio.run(tts.synthesize(
        text="The baby weight is 3.2 kg and OPV-1 is due.",
        language_code="kn-IN",
        voice="Kavya"
    ))
    assert len(audio_bytes) > 44  # WAV header is 44 bytes
    assert audio_bytes[:4] == b"RIFF"
    assert audio_bytes[8:12] == b"WAVE"


def test_get_voice_status_route():
    data = asyncio.run(get_voice_status())
    assert data["status"] == "ready"
    assert data["gnani_stt_model"] == "prisma-v3.0"
    assert data["gnani_tts_model"] == "timbre-v2.5"
    assert len(data["supported_languages"]) == 10
    assert any(lang["code"] == "hi-IN" for lang in data["supported_languages"])
    assert any(lang["code"] == "kn-IN" for lang in data["supported_languages"])
    assert any(lang["code"] == "ta-IN" for lang in data["supported_languages"])


def test_tts_route():
    """Tests POST /api/voice/tts endpoint."""
    payload = TTSRequestPayload(
        text="ಮಗುವಿನ ತೂಕ 3.2 ಕೆಜಿ ಇದೆ",
        language="kn-IN",
        voice="Kavya",
        speed=1.0
    )
    res = asyncio.run(synthesize_speech(payload))
    assert res.media_type == "audio/wav"
    assert len(res.body) > 44
    assert res.headers["X-Language"] == "kn-IN"


def test_send_to_phase2_route():
    payload = Phase2TranscriptPayload(
        transcript="बच्चे का वजन 3.2 किलोग्राम है",
        language="hi",
        status="completed"
    )
    res = asyncio.run(send_to_phase2(payload))
    assert res["success"] is True
    assert res["payload"]["transcript"] == payload.transcript

    history = asyncio.run(get_recent_transcripts())
    assert history["count"] >= 1


# --- 5 REQUIRED TARGETED TESTS FOR SILENCE, VAD, FAILURE & ISOLATION ---

def test_microphone_silence_detection():
    """
    Test 1: Microphone is ON, but the user is silent.
    Verifies that:
    - Audio processor classifies frames as non-speech.
    - Gating sets should_forward to False.
    - has_detected_speech() remains False.
    - Phase 2 contract produces empty transcript without phantom words.
    - Mock engine generates NO simulated text on silence.
    """
    processor = AudioProcessor(sample_rate=16000, silence_threshold=200.0)
    mock_eng = MockTranscriptionEngine(language_code="kn-IN")

    # Feed 10 chunks of pure silence (amplitude=0)
    for _ in range(10):
        silent_pcm = generate_dummy_pcm(50, amplitude=0)
        is_valid, rms, metrics = processor.process_pcm_chunk(silent_pcm)
        assert is_valid is True
        assert rms == 0.0
        assert metrics["is_speech"] is False
        assert metrics["should_forward"] is False
        mock_eng.register_audio_chunk(len(silent_pcm), is_speech=metrics["is_speech"])

    assert processor.has_detected_speech() is False
    assert processor.is_silent_session() is True
    assert mock_eng.has_detected_speech() is False

    # Verify mock engine event on silence returns type 'silence' with empty transcript
    silence_event = asyncio.run(mock_eng.generate_mock_event())
    assert silence_event["type"] == "silence"
    assert silence_event["transcript"] == ""

    # Verify final payload returns empty transcript
    payload = AudioProcessor.format_phase2_payload(transcript="", language_code="kn-IN")
    assert payload["transcript"] == ""
    assert payload["language"] == "kn"
    assert payload["status"] == "completed"

    mock_final = mock_eng.get_final_payload()
    assert mock_final["transcript"] == ""
    assert mock_final["speech_detected"] is False


def test_actual_spoken_input():
    """
    Test 2: Actual spoken input with active voice energy.
    Verifies that:
    - Audio processor detects speech (RMS >= silence_threshold).
    - should_forward is True.
    - has_detected_speech() becomes True.
    - Consecutive speech chunks are tracked.
    - Hangover buffer activates.
    """
    processor = AudioProcessor(sample_rate=16000, silence_threshold=200.0, vad_hangover_frames=5)
    speech_pcm = generate_dummy_pcm(50, amplitude=2500)

    # First speech chunk
    is_valid, rms, metrics = processor.process_pcm_chunk(speech_pcm)
    assert is_valid is True
    assert rms > 200.0
    assert metrics["is_speech"] is True
    assert metrics["should_forward"] is True

    # Second speech chunk (confirms speech session)
    is_valid, rms, metrics = processor.process_pcm_chunk(speech_pcm)
    assert processor.has_detected_speech() is True
    assert processor.is_silent_session() is False
    assert metrics["speech_chunks"] == 2

    # Trailing silence chunk within hangover window should still forward
    silent_pcm = generate_dummy_pcm(50, amplitude=0)
    is_valid, rms, metrics = processor.process_pcm_chunk(silent_pcm)
    assert metrics["is_speech"] is False
    assert metrics["should_forward"] is True  # preserved by hangover buffer!


def test_background_noise_classification():
    """
    Test 3: Ambient background noise / mic hiss below speech threshold.
    Verifies that:
    - Low-amplitude noise (RMS < 200) is filtered out.
    - is_speech is False.
    - should_forward is False.
    - Background noise alone NEVER triggers speech session.
    """
    processor = AudioProcessor(sample_rate=16000, silence_threshold=200.0)

    # Ambient room noise / fan hum / mic electrical hiss (amplitude ~100 -> RMS ~100)
    noise_pcm = generate_dummy_pcm(50, amplitude=100)
    for _ in range(8):
        is_valid, rms, metrics = processor.process_pcm_chunk(noise_pcm)
        assert is_valid is True
        assert rms < 200.0
        assert metrics["is_speech"] is False
        assert metrics["should_forward"] is False

    assert processor.has_detected_speech() is False
    assert processor.is_silent_session() is True


def test_gnani_connection_failure_no_mock_fallback():
    """
    Test 4: When Gnani Prisma connection fails in live mode,
    verifies that:
    - The server returns an explicit error message (GNANI_CONNECTION_FAILED).
    - The server does NOT silently fall back to MockTranscriptionEngine.
    - The server terminates the session with code 1011.
    """
    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []
            self.closed_code = None
            self.closed_reason = None
            self.accepted = False

        async def accept(self):
            self.accepted = True

        async def send_text(self, text: str):
            self.sent_messages.append(json.loads(text))

        async def close(self, code: int = 1000, reason: str = ""):
            self.closed_code = code
            self.closed_reason = reason

        async def receive(self):
            return {"text": json.dumps({"action": "stop"})}

    mock_ws = MockWebSocket()

    with patch.object(VoiceConfig, "has_real_credentials", new_callable=PropertyMock, return_value=True):
        with patch("websockets.connect", side_effect=ConnectionRefusedError("Connection refused by upstream host")):
            asyncio.run(voice_streaming_endpoint(mock_ws, language="indic-auto"))

    assert mock_ws.accepted is True
    # Verify error was sent
    assert len(mock_ws.sent_messages) == 1
    err = mock_ws.sent_messages[0]
    assert err["type"] == "error"
    assert err["code"] == "GNANI_CONNECTION_FAILED"
    assert err["is_mock"] is False
    assert "Connection refused" in err["message"]
    # Verify connection was terminated with 1011 and mock engine was NEVER invoked
    assert mock_ws.closed_code == 1011


def test_mock_fallback_isolation_in_live_mode():
    """
    Test 5: Live production mode isolation.
    Verifies that:
    - When real credentials exist, active_stt_engine is 'gnani_prisma_v3'.
    - simulation_notice is None.
    - Fallback mock engine is never used in live status.
    """
    with patch.object(VoiceConfig, "has_real_credentials", new_callable=PropertyMock, return_value=True):
        status_data = asyncio.run(get_voice_status())
        assert status_data["has_gnani_credentials"] is True
        assert status_data["active_stt_engine"] == "gnani_prisma_v3"
        assert status_data["active_tts_engine"] == "gnani_timbre_v2.5"
        assert status_data["simulation_notice"] is None

    with patch.object(VoiceConfig, "has_real_credentials", new_callable=PropertyMock, return_value=False):
        status_data_mock = asyncio.run(get_voice_status())
        assert status_data_mock["has_gnani_credentials"] is False
        assert status_data_mock["active_stt_engine"] == "mock_simulation"
        assert status_data_mock["simulation_notice"] is not None


def test_gnani_transcript_text_field_normalization():
    """
    Verifies that when Gnani Prisma returns {"type": "transcript", "text": "...", "is_final": True},
    gnani_client normalizes both 'text' and 'transcript' fields.
    """
    client = GnaniPrismaClient(language_code="en-IN")
    
    # Mock upstream websocket iterator returning Gnani's exact JSON format
    raw_gnani_json = json.dumps({
        "type": "transcript",
        "text": "The baby weight is 3.2 kilograms, and vaccination is due.",
        "is_final": True,
        "detected_language_code": "en-IN"
    })
    
    class FakeWS:
        def __aiter__(self):
            return self
        async def __anext__(self):
            if hasattr(self, "_done"):
                raise StopAsyncIteration
            self._done = True
            return raw_gnani_json

    client.ws = FakeWS()
    
    events = []
    async def collect():
        async for ev in client.receive_events():
            events.append(ev)
            
    asyncio.run(collect())
    assert len(events) == 1
    ev = events[0]
    assert ev["type"] == "transcript"
    assert ev["text"] == "The baby weight is 3.2 kilograms, and vaccination is due."
    assert ev["transcript"] == "The baby weight is 3.2 kilograms, and vaccination is due."
    assert ev["is_final"] is True
    assert ev["engine"] == "gnani_prisma_v3"

