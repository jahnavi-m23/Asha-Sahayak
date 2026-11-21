# backend/ai/phase3_client.py
"""
Phase 3 Client & Dispatcher.
Transmits confirmed records to the shared backend register / Phase 3 persistence module.
Adheres strictly to the required common JSON structure:
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
import logging
from typing import Dict, Any, Optional
import httpx

from backend.config import settings
from backend.models.schemas import FieldExtractionOutput, Phase3RecordPayload

logger = logging.getLogger("asha_sahayak.ai.phase3_client")


class Phase3Client:
    """Client for Phase 3 shared backend communication."""

    def __init__(self, endpoint_url: Optional[str] = None):
        self.endpoint_url = endpoint_url or settings.PHASE_3_ENDPOINT_URL
        self.api_key = settings.PHASE_3_API_KEY
        self.offline_queue = []  # In-memory store for offline buffering

    def build_phase3_payload(self, record: FieldExtractionOutput) -> Phase3RecordPayload:
        """Convert internal FieldExtractionOutput to strict Phase 3 JSON contract."""
        danger_signs_dict = [
            {
                "code": ds.code,
                "name": ds.name,
                "severity": ds.severity.value,
                "is_negated": ds.is_negated,
                "guideline_source": ds.guideline_source,
                "referral_instruction": ds.referral_instruction_en
            }
            for ds in record.danger_signs
            if not ds.is_negated
        ]

        return Phase3RecordPayload(
            beneficiary_id=record.beneficiary_id,
            visit_type=record.visit_type or "Newborn home visit",
            weight=record.weight,
            vaccinations_due=record.vaccinations_due,
            next_visit_date=record.next_visit_date,
            danger_signs=danger_signs_dict,
            referral_required=record.referral_required,
            confirmation_status="confirmed"
        )

    async def send_confirmed_record(
        self,
        record: FieldExtractionOutput,
        client: Optional[httpx.AsyncClient] = None
    ) -> Dict[str, Any]:
        """
        Send confirmed record to Phase 3 endpoint.
        Gracefully handles offline mode by buffering in self.offline_queue.
        """
        payload = self.build_phase3_payload(record)
        payload_data = payload.model_dump()

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            if client:
                response = await client.post(
                    self.endpoint_url,
                    json=payload_data,
                    headers=headers
                )
                response.raise_for_status()
            else:
                async with httpx.AsyncClient(timeout=1.0) as local_client:
                    response = await local_client.post(
                        self.endpoint_url,
                        json=payload_data,
                        headers=headers
                    )
                    response.raise_for_status()

            return {
                "success": True,
                "synced": True,
                "status_code": response.status_code,
                "data": payload_data,
                "phase3_response": response.json() if "json" in response.headers.get("content-type", "") else response.text
            }
        except Exception as e:
            logger.warning(
                "Phase 3 server offline or unreachable at %s (%s). Buffering confirmed record locally.",
                self.endpoint_url, str(e)
            )
            # Store in offline queue
            self.offline_queue.append(payload_data)
            return {
                "success": True,
                "synced": False,
                "buffered_locally": True,
                "data": payload_data,
                "note": f"Saved locally in Phase 2 queue; will sync when Phase 3 is reachable. Reason: {str(e)}"
            }
