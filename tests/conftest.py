# tests/conftest.py
"""Pytest fixtures for Phase 2 test suite."""
import pytest
import httpx
from backend.main import app
from backend.models.schemas import FieldExtractionOutput, ConfirmationStatus
from backend.safety.danger_signs import DangerSignDetector
from backend.ai.qwen_extractor import QwenExtractor
from backend.ai.voice_readback import VoiceReadbackService
from backend.ai.voice_corrector import VoiceCorrectionHandler
from backend.ai.phase3_client import Phase3Client


@pytest.fixture
def danger_detector():
    """DangerSignDetector instance."""
    return DangerSignDetector()


@pytest.fixture
def qwen_extractor(danger_detector):
    """QwenExtractor instance."""
    return QwenExtractor(danger_detector=danger_detector)


@pytest.fixture
def voice_service():
    """VoiceReadbackService instance."""
    return VoiceReadbackService()


@pytest.fixture
def voice_corrector(danger_detector):
    """VoiceCorrectionHandler instance."""
    return VoiceCorrectionHandler(danger_detector=danger_detector)


@pytest.fixture
def phase3_client():
    """Phase3Client instance."""
    return Phase3Client()


@pytest.fixture
def sample_pending_record():
    """Sample extraction record in pending state."""
    return FieldExtractionOutput(
        beneficiary_id="BNF-2041",
        visit_type="Newborn home visit",
        weight="3.2 kg",
        vaccinations_due=["OPV-1"],
        next_visit_date=None,
        missing_fields=["next_visit_date"],
        danger_signs=[],
        referral_required=False,
        confirmation_status=ConfirmationStatus.PENDING,
        readback_text="Baby weight is 3.2 kg. OPV-1 vaccination is due. Is this correct?"
    )


@pytest.fixture
async def async_client():
    """Asynchronous in-process ASGI test client."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver"
    ) as client:
        yield client
