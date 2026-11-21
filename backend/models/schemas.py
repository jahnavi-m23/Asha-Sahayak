# backend/models/schemas.py
"""
Data schemas and API contracts for ASHA SAHAYAK Phase 2.
Implements the exact JSON structures required by Phase 1 inputs and Phase 3 handoff.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class SupportedLanguage(str, Enum):
    """Supported languages and code-mix configurations for ASHA workers."""
    KANNADA = "kn"
    ENGLISH = "en"
    KANNADA_ENGLISH = "kn-en"


class ConfirmationStatus(str, Enum):
    """Status of worker record confirmation."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class DangerSignSeverity(str, Enum):
    """Severity level of detected danger signs according to public health guidelines."""
    CRITICAL_EMERGENCY = "critical_emergency"  # Immediate referral to FRU / CHC
    HIGH = "high"                              # Urgent referral to PHC
    UNCERTAIN = "uncertain"                    # Flagged for human/clinical review


class DangerSignDetection(BaseModel):
    """Structured representation of a detected maternal/neonatal danger sign."""
    code: str = Field(..., description="Standardized guideline code, e.g. HBNC-DS-01")
    name: str = Field(..., description="Danger sign title in English")
    name_kannada: Optional[str] = Field(None, description="Danger sign title in Kannada")
    severity: DangerSignSeverity = Field(..., description="Severity level")
    category: str = Field(..., description="Category: newborn, pregnancy, postpartum, general")
    matched_phrase: str = Field(..., description="The transcript phrase triggering the detection")
    is_negated: bool = Field(default=False, description="Whether negation was detected")
    is_uncertain: bool = Field(default=False, description="Flagged for human verification")
    guideline_source: str = Field(..., description="Public health guideline citation")
    referral_instruction_en: str = Field(..., description="Urgent referral advice in English")
    referral_instruction_kn: str = Field(..., description="Urgent referral advice in Kannada")


class Phase1TranscriptInput(BaseModel):
    """
    Input received from Phase 1 speech-to-text module.
    Example:
    {
      "transcript": "The baby weight is 3.2 kg and OPV-1 is due.",
      "language": "kn-en",
      "status": "completed"
    }
    """
    transcript: str = Field(..., min_length=1, description="Raw transcript from Phase 1 STT")
    language: str = Field(default="kn-en", description="Detected or selected language (kn, en, kn-en)")
    status: str = Field(default="completed", description="Phase 1 status (must be 'completed' for processing)")
    beneficiary_id: Optional[str] = Field(default=None, description="Pre-selected beneficiary ID if known")
    session_id: Optional[str] = Field(default=None, description="Voice interaction session ID")


class FieldExtractionOutput(BaseModel):
    """
    Structured extraction output as mandated by the project specification.
    Example:
    {
      "beneficiary_id": "BNF-2041",
      "visit_type": "Newborn home visit",
      "weight": "3.2 kg",
      "vaccinations_due": ["OPV-1"],
      "next_visit_date": null,
      "missing_fields": ["next_visit_date"],
      "danger_signs": [],
      "referral_required": false,
      "confirmation_status": "pending"
    }
    """
    beneficiary_id: Optional[str] = Field(
        default=None,
        description="Beneficiary ID, when provided or selected from an authorized beneficiary record"
    )
    visit_type: Optional[str] = Field(
        default=None,
        description="Standardized visit type: Newborn home visit, ANC, PNC, Routine immunization, etc."
    )
    weight: Optional[str] = Field(
        default=None,
        description="Measured weight formatted with units, e.g., '3.2 kg'"
    )
    age: Optional[str] = Field(
        default=None,
        description="Extracted age of infant or child, e.g., '6 weeks', '2 months', '10 days'"
    )
    vaccinations_due: List[str] = Field(
        default_factory=list,
        description="List of standardized vaccines due, e.g. ['OPV-1', 'BCG']"
    )
    next_visit_date: Optional[str] = Field(
        default=None,
        description="Next visit date formatted as YYYY-MM-DD or null"
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="List of required or expected fields that were not found in the transcript"
    )
    uncertain_fields: List[str] = Field(
        default_factory=list,
        description="List of fields flagged as ambiguous or uncertain rather than guessed"
    )
    danger_signs: List[DangerSignDetection] = Field(
        default_factory=list,
        description="List of detected danger signs according to public health guidelines"
    )
    referral_required: bool = Field(
        default=False,
        description="True if one or more actionable danger signs are present"
    )
    confirmation_status: ConfirmationStatus = Field(
        default=ConfirmationStatus.PENDING,
        description="Current record confirmation status: pending, in_review, confirmed"
    )
    
    # Conversational assistance fields for the ASHA worker
    clarification_prompt: Optional[str] = Field(
        default=None,
        description="Targeted clarification question in worker's language for missing fields"
    )
    readback_text: Optional[str] = Field(
        default=None,
        description="Full text for Gnani Timbre voice read-back"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session tracker for conversational corrections"
    )

    @field_validator("weight")
    @classmethod
    def validate_weight_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        # Normalization: ensure weight has 'kg' or 'g'
        if v.replace(".", "", 1).isdigit():
            # If purely numeric, default to kg
            return f"{v} kg"
        return v


class CorrectionRequest(BaseModel):
    """
    ASHA worker voice or text correction request.
    Example: "No, weight is 2.8 kilograms."
    """
    session_id: Optional[str] = Field(None, description="Associated session ID")
    correction_transcript: str = Field(..., min_length=1, description="Voice correction utterance")
    language: str = Field(default="kn-en", description="Utterance language (kn, en, kn-en)")
    current_record: FieldExtractionOutput = Field(..., description="The current unconfirmed record state")


class ConfirmationRequest(BaseModel):
    """
    Explicit confirmation request from the ASHA worker.
    The record can only be sent to Phase 3 when explicitly confirmed.
    """
    session_id: Optional[str] = Field(None, description="Session ID")
    confirmed: bool = Field(..., description="Whether worker explicitly confirmed the record")
    record: FieldExtractionOutput = Field(..., description="The record to confirm")


class Phase3RecordPayload(BaseModel):
    """
    Common JSON structure delivered to Phase 3 after explicit worker confirmation.
    Exact contract:
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
    beneficiary_id: Optional[str] = Field(..., description="Beneficiary ID")
    visit_type: Optional[str] = Field(..., description="Visit type")
    weight: Optional[str] = Field(..., description="Recorded weight")
    vaccinations_due: List[str] = Field(..., description="Vaccines due")
    next_visit_date: Optional[str] = Field(..., description="Next scheduled visit date or null")
    danger_signs: List[Dict[str, Any]] = Field(default_factory=list, description="Danger sign details")
    referral_required: bool = Field(..., description="Whether referral is required")
    confirmation_status: str = Field("confirmed", description="Always 'confirmed' for Phase 3 persistence")


class VoiceReadbackResponse(BaseModel):
    """Voice readback synthesis output."""
    readback_text: str = Field(..., description="Text read back to the worker")
    language: str = Field(..., description="Language used for synthesis")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio from Gnani Timbre")
    audio_format: str = Field("wav", description="Audio container format (wav, mp3)")
    is_mock: bool = Field(default=False, description="Whether fallback mock audio was generated")


class InteractionState(BaseModel):
    """Internal session state tracking conversational flow."""
    session_id: str
    record: FieldExtractionOutput
    history: List[Dict[str, str]] = Field(default_factory=list)
    awaiting_field: Optional[str] = None
