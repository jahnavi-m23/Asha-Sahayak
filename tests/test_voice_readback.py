# tests/test_voice_readback.py
"""
Tests for Gnani Timbre v3.0 voice read-back synthesis.
"""
import pytest
from backend.models.schemas import VoiceReadbackResponse


@pytest.mark.asyncio
async def test_voice_readback_synthesis_english(voice_service):
    text = "Baby weight is 3.2 kilograms. OPV-1 vaccination is due. Is this correct?"
    resp: VoiceReadbackResponse = await voice_service.synthesize_speech(text, language="en")
    
    assert resp.readback_text == text
    assert resp.language == "en-IN"
    assert resp.audio_base64 is not None
    assert len(resp.audio_base64) > 20
    assert resp.audio_format == "wav"


@pytest.mark.asyncio
async def test_voice_readback_synthesis_kannada(voice_service):
    text = "ಮಗುವಿನ ತೂಕ 3.2 ಕಿಲೋಗ್ರಾಂ. OPV-1 ಲಸಿಕೆ ಬಾಕಿ ಇದೆ. ಇದು ಸರಿಯೇ?"
    resp: VoiceReadbackResponse = await voice_service.synthesize_speech(text, language="kn")
    
    assert resp.readback_text == text
    assert resp.language == "kn-IN"
    assert resp.audio_base64 is not None


@pytest.mark.asyncio
async def test_voice_readback_code_mixed(voice_service):
    text = "Baby weight 3.2 kg ide. OPV-1 vaccine due ide. Is this correct?"
    resp: VoiceReadbackResponse = await voice_service.synthesize_speech(text, language="kn-en")
    
    assert resp.readback_text == text
    assert resp.language == "kn-IN"


@pytest.mark.asyncio
async def test_gnani_timbre_live_wire_protocol(voice_service, monkeypatch):
    """Verify live Gnani Timbre v3.0 wire request structure and headers."""
    import httpx
    import json
    import base64

    captured_request = {}

    def mock_gnani_handler(request: httpx.Request):
        captured_request["url"] = str(request.url)
        captured_request["auth"] = request.headers.get("Authorization")
        captured_request["x_api_key"] = request.headers.get("x-api-key")
        captured_request["body"] = json.loads(request.read())

        # Return simulated Gnani Timbre JSON with audio content
        sample_audio = base64.b64encode(b"RIFF....WAVEfmt ....data....").decode("ascii")
        return httpx.Response(
            200,
            json={"audio_content": sample_audio, "status": "success"},
            headers={"content-type": "application/json"}
        )

    voice_service.api_key = "gnani-api-key-test"
    voice_service.token = "gnani-token-test"

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_gnani_handler))

    async def mock_call(text, gnani_lang):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {voice_service.token or voice_service.api_key}",
            "x-api-key": voice_service.api_key or ""
        }
        payload = {
            "text": text,
            "language": gnani_lang,
            "audio_format": "wav",
            "speed": 1.0,
            "sample_rate": 16000
        }
        resp = await mock_client.post(voice_service.api_url, headers=headers, json=payload)
        resp.raise_for_status()
        res_data = resp.json()
        return VoiceReadbackResponse(
            readback_text=text,
            language=gnani_lang,
            audio_base64=res_data["audio_content"],
            audio_format="wav",
            is_mock=False
        )

    monkeypatch.setattr(voice_service, "_call_gnani_api", mock_call)

    resp = await voice_service.synthesize_speech("Baby weight is 3.2 kg.", language="en")

    assert captured_request["x_api_key"] == "gnani-api-key-test"
    assert "Bearer gnani-token-test" in captured_request["auth"]
    assert captured_request["body"]["language"] == "en-IN"
    assert captured_request["body"]["audio_format"] == "wav"
    assert resp.is_mock is False
    assert resp.audio_base64 is not None
