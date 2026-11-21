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


import inspect

def _run_coroutine_clean(coro):
    """
    Direct in-memory coroutine driver for Windows sandbox environments.
    Avoids asyncio ProactorEventLoop and socket.socketpair() hangs on Windows.
    """
    stack = [coro]
    val = None
    exc = None
    while stack:
        top = stack[-1]
        try:
            if exc:
                curr_exc = exc
                exc = None
                nxt = top.throw(curr_exc)
            else:
                nxt = top.send(val)
                val = None
            if inspect.iscoroutine(nxt):
                stack.append(nxt)
            else:
                val = nxt
        except StopIteration as e:
            stack.pop()
            val = e.value
        except Exception as e:
            stack.pop()
            exc = e
            if not stack:
                raise
    return val

def pytest_pyfunc_call(pyfuncitem):
    """Hook to execute async test functions directly without pytest-asyncio plugin."""
    testfunction = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunction):
        testargs = {
            arg: pyfuncitem.funcargs[arg]
            for arg in pyfuncitem._fixtureinfo.argnames
        }
        _run_coroutine_clean(testfunction(**testargs))
        return True
    return None


@pytest.fixture
def async_client():
    """Asynchronous in-process ASGI test client."""
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver"
    )
    yield client

