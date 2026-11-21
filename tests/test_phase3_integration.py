# tests/test_phase3_integration.py
"""
Tests for Phase 3 common JSON structure generation and dispatch.
Contract:
{
  "beneficiary_id": "BNF-2041",
  "visit_type": "Newborn home visit",
  "weight": "3.2 kg",
  "vaccinations_due": ["OPV-1"],
  "next_visit_date": null,
  "danger_signs": [],
  "referral_required": false,
  "confirmation_status": "confirmed"
}
"""
import pytest
import httpx
from backend.models.schemas import ConfirmationStatus, Phase3RecordPayload


def test_phase3_payload_structure(phase3_client, sample_pending_record):
    sample_pending_record.confirmation_status = ConfirmationStatus.CONFIRMED
    payload: Phase3RecordPayload = phase3_client.build_phase3_payload(sample_pending_record)

    data = payload.model_dump()
    assert data["beneficiary_id"] == "BNF-2041"
    assert data["visit_type"] == "Newborn home visit"
    assert data["weight"] == "3.2 kg"
    assert data["vaccinations_due"] == ["OPV-1"]
    assert data["next_visit_date"] is None
    assert data["danger_signs"] == []
    assert data["referral_required"] is False
    assert data["confirmation_status"] == "confirmed"


@pytest.mark.asyncio
async def test_phase3_client_send_record_offline_buffering(phase3_client, sample_pending_record):
    sample_pending_record.confirmation_status = ConfirmationStatus.CONFIRMED
    # Mock offline server returning a connection error
    def raise_connect_error(request):
        raise httpx.ConnectError("Connection refused by target machine")

    mock_offline_transport = httpx.MockTransport(raise_connect_error)
    async with httpx.AsyncClient(transport=mock_offline_transport) as mock_client:
        result = await phase3_client.send_confirmed_record(sample_pending_record, client=mock_client)

        # When Phase 3 server is offline, client buffers locally and returns success=True
        assert result["success"] is True
        assert result["synced"] is False
        assert len(phase3_client.offline_queue) >= 1
        assert phase3_client.offline_queue[-1]["beneficiary_id"] == "BNF-2041"
        assert phase3_client.offline_queue[-1]["confirmation_status"] == "confirmed"


@pytest.mark.asyncio
async def test_phase3_client_send_record_online_success(phase3_client, sample_pending_record):
    sample_pending_record.confirmation_status = ConfirmationStatus.CONFIRMED
    # Mock online server response
    mock_transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"status": "saved", "id": "REC-123"})
    )
    async with httpx.AsyncClient(transport=mock_transport) as mock_client:
        result = await phase3_client.send_confirmed_record(sample_pending_record, client=mock_client)
        assert result["success"] is True
        assert result["synced"] is True
        assert result["status_code"] == 200
