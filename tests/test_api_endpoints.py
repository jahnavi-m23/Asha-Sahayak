# tests/test_api_endpoints.py
"""
Tests for FastAPI HTTP endpoints in backend/routes/ai.py using async ASGI client.
"""
import pytest
from backend.models.schemas import ConfirmationStatus


@pytest.mark.asyncio
async def test_root_endpoint(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "ASHA SAHAYAK"
    assert data["phase"] == "Phase 2: AI Understanding, Data Extraction and Safety"


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/api/ai/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["phase"] == 2
    assert data["danger_signs_rules_loaded"] > 5


@pytest.mark.asyncio
async def test_danger_signs_rules_endpoint(async_client):
    response = await async_client.get("/api/ai/danger-signs/rules")
    assert response.status_code == 200
    data = response.json()
    assert data["total_rules"] > 0
    assert "MoHFW Home Based Newborn Care" in data["guidelines"][0]


@pytest.mark.asyncio
async def test_process_transcript_endpoint(async_client):
    payload = {
        "transcript": "The baby weight is 3.2 kg and OPV-1 is due.",
        "language": "kn-en",
        "status": "completed",
        "beneficiary_id": "BNF-2041"
    }
    response = await async_client.post("/api/ai/process-transcript", json=payload)
    assert response.status_code == 200
    data = response.json()
    record = data["record"]
    assert record["beneficiary_id"] == "BNF-2041"
    assert record["weight"] == "3.2 kg"
    assert "OPV-1" in record["vaccinations_due"]
    assert record["confirmation_status"] == "pending"
    assert "voice_readback" in data
    assert data["voice_readback"]["audio_base64"] is not None


@pytest.mark.asyncio
async def test_correct_record_endpoint(async_client, sample_pending_record):
    payload = {
        "correction_transcript": "No, weight is 2.8 kilograms.",
        "language": "en",
        "current_record": sample_pending_record.model_dump()
    }
    response = await async_client.post("/api/ai/correct-record", json=payload)
    assert response.status_code == 200
    data = response.json()
    record = data["record"]
    assert record["weight"] == "2.8 kg"
    assert record["confirmation_status"] == "in_review"
    assert record["beneficiary_id"] == "BNF-2041"


@pytest.mark.asyncio
async def test_confirm_record_endpoint(async_client, sample_pending_record):
    payload = {
        "confirmed": True,
        "record": sample_pending_record.model_dump()
    }
    response = await async_client.post("/api/ai/confirm-record", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["record"]["confirmation_status"] == "confirmed"
    assert "phase3_handoff" in data


@pytest.mark.asyncio
async def test_confirm_record_declined(async_client, sample_pending_record):
    payload = {
        "confirmed": False,
        "record": sample_pending_record.model_dump()
    }
    response = await async_client.post("/api/ai/confirm-record", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unconfirmed"


@pytest.mark.asyncio
async def test_synthesize_speech_endpoint(async_client):
    payload = {
        "text": "ಮಗುವಿನ ತೂಕ 3.2 ಕಿಲೋಗ್ರಾಂ. OPV-1 ಲಸಿಕೆ ಬಾಕಿ ಇದೆ.",
        "language": "kn"
    }
    response = await async_client.post("/api/ai/synthesize-speech", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["audio_base64"] is not None
    assert data["language"] == "kn-IN"
