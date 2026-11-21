import math
import re
import struct
from typing import Tuple, Dict, Any, List
from backend.voice.config import SUPPORTED_LANGUAGES, SPECIAL_STT_MODES
from backend.voice.medical_vocabulary import VERIFIED_FIND_AND_REPLACE

class AudioProcessor:
    """
    Handles PCM audio validation, volume RMS energy calculation,
    adaptive background noise floor estimation, voice activity detection (VAD),
    and verified clinical normalization.
    Audio format: Raw 16-bit Linear PCM, 16000 Hz, Single Channel (Mono), Little-Endian.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        silence_threshold: float = 200.0,
        vad_hangover_frames: int = 15
    ):
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.vad_hangover_frames = vad_hangover_frames
        
        # Audio streaming metrics
        self.total_bytes_processed = 0
        self.silent_chunks_count = 0
        self.speech_chunks_count = 0
        self.consecutive_silent_chunks = 0
        self.consecutive_speech_chunks = 0
        self.hangover_chunks = 0
        
        # Adaptive background noise tracking for rural field environments
        self.estimated_noise_floor = 50.0  # Initial baseline estimate
        self.noise_samples_count = 0

    def process_pcm_chunk(self, chunk: bytes) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Processes a raw PCM 16-bit mono chunk:
        - Validates frame byte alignment
        - Computes RMS volume energy
        - Updates adaptive noise floor from ambient silence
        - Dynamically gates speech vs background noise (fans, traffic, street hiss)
        - Applies hangover buffer to prevent clipping word endings
        Returns (is_valid, rms, metrics)
        """
        if not chunk or len(chunk) % 2 != 0:
            return False, 0.0, {"error": "Invalid PCM chunk size (must be even number of bytes for 16-bit)"}

        num_samples = len(chunk) // 2
        # Unpack 16-bit signed little-endian integers
        samples = struct.unpack(f"<{num_samples}h", chunk)
        
        # Calculate Root Mean Square (RMS) energy
        sum_squares = sum(s * s for s in samples)
        rms = math.sqrt(sum_squares / num_samples) if num_samples > 0 else 0.0

        self.total_bytes_processed += len(chunk)

        # Adaptive threshold: dynamically adapt above ambient noise floor
        # In rural clinics with fan/street noise, noise floor can rise to 120-180 RMS
        effective_threshold = max(self.silence_threshold, 1.8 * self.estimated_noise_floor)
        is_speech = rms >= effective_threshold

        if is_speech:
            self.speech_chunks_count += 1
            self.consecutive_speech_chunks += 1
            self.consecutive_silent_chunks = 0
            self.hangover_chunks = self.vad_hangover_frames
            should_forward = True
        else:
            self.silent_chunks_count += 1
            self.consecutive_silent_chunks += 1
            self.consecutive_speech_chunks = 0
            
            # Smoothly adapt background noise floor estimate using EMA on non-speech frames
            self.estimated_noise_floor = 0.96 * self.estimated_noise_floor + 0.04 * rms
            self.noise_samples_count += 1

            if self.hangover_chunks > 0:
                self.hangover_chunks -= 1
                should_forward = True
            else:
                should_forward = False

        metrics = {
            "num_samples": num_samples,
            "rms": round(rms, 2),
            "noise_floor": round(self.estimated_noise_floor, 2),
            "effective_threshold": round(effective_threshold, 2),
            "is_speech": is_speech,
            "should_forward": should_forward,
            "speech_chunks": self.speech_chunks_count,
            "silent_chunks": self.silent_chunks_count,
            "total_bytes": self.total_bytes_processed,
            "duration_seconds": round(self.total_bytes_processed / (self.sample_rate * 2), 2)
        }
        return True, rms, metrics

    def has_detected_speech(self) -> bool:
        """
        Returns True only if actual speech energy was detected.
        Requires at least 2 speech chunks (~64ms) to filter out transient pops/clicks.
        """
        return self.speech_chunks_count >= 2

    def is_silent_session(self) -> bool:
        """Returns True if the entire recorded session contains no speech."""
        return self.speech_chunks_count < 2

    def get_speech_quality_summary(self) -> Dict[str, Any]:
        """Provides a summary of audio quality and speech clarity."""
        total_chunks = self.silent_chunks_count + self.speech_chunks_count
        speech_ratio = (self.speech_chunks_count / total_chunks) if total_chunks > 0 else 0.0
        
        is_silent = total_chunks > 5 and self.speech_chunks_count < 2
        is_unclear = total_chunks > 15 and 0 < speech_ratio < 0.15
        
        return {
            "total_chunks": total_chunks,
            "speech_chunks": self.speech_chunks_count,
            "silent_chunks": self.silent_chunks_count,
            "speech_ratio": round(speech_ratio, 2),
            "noise_floor_estimate": round(self.estimated_noise_floor, 2),
            "is_silent": is_silent,
            "is_unclear_or_silent": is_unclear or is_silent,
            "recommendation": (
                "ಯಾವುದೇ ಧ್ವನಿ ಪತ್ತೆಯಾಗಿಲ್ಲ (ಮೌನ) / No speech detected. Audio is silent."
                if is_silent else
                "ಧ್ವನಿ ಅಸ್ಪಷ್ಟವಾಗಿದೆ ಅಥವಾ ಧ್ವನಿ ಮಟ್ಟ ಕಡಿಮೆ ಇದೆ, ದಯವಿಟ್ಟು ಮೈಕ್ರೊಫೋನ್‌ಗೆ ಹತ್ತಿರವಾಗಿ ಮಾತನಾಡಿ / Audio level is low or unclear. Please speak closer to the microphone."
                if is_unclear else "Good"
            )
        }

    @staticmethod
    def map_language_to_phase2(lang_code: str) -> str:
        """
        Maps API language codes to Phase 2 contract for all 10 Indian languages.
        """
        clean = lang_code.lower().strip()

        if "indic-auto" in clean or clean == "auto":
            return "auto"
        if "kn" in clean and "en" in clean:
            return "kn-en"
        if "hi" in clean and "en" in clean:
            return "hi-en"

        for code, info in SUPPORTED_LANGUAGES.items():
            prefix = info["phase2_code"]
            if prefix in clean or code.lower() in clean:
                return prefix

        return clean[:2] if len(clean) >= 2 else "kn"

    @staticmethod
    def apply_verified_medical_normalization(raw_text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Applies verified find-and-replace rules for clinical abbreviations and units.
        Preserves the meaning of original speech.
        Returns:
            (normalized_text, audit_trail_of_corrections)
        """
        if not raw_text or not raw_text.strip():
            return "", []

        normalized = raw_text
        corrections: List[Dict[str, str]] = []

        for pattern, replacement in VERIFIED_FIND_AND_REPLACE:
            # Check if pattern matches
            matches = list(re.finditer(pattern, normalized, flags=re.IGNORECASE))
            if matches:
                for match in matches:
                    corrections.append({
                        "original": match.group(0),
                        "normalized": replacement,
                        "rule": pattern
                    })
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        # Clean multiple spaces resulting from replacements
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized, corrections

    @staticmethod
    def detect_clinical_markers(text: str) -> Dict[str, Any]:
        """
        Detects critical clinical markers including numbers, weights, BP, vaccinations,
        and explicit negations across Kannada and English.
        """
        if not text:
            return {"has_numbers": False, "has_negation": False, "detected_markers": []}

        markers: List[str] = []

        # 1. Decimal weights / measurements (e.g. 2.8 kg, 3.2 kg, 120/80)
        has_weight = bool(re.search(r"\b\d+(\.\d+)?\s*(kg|grams?|ಕೆಜಿ)\b", text, re.IGNORECASE))
        has_bp = bool(re.search(r"\b\d{2,3}[/\s]\d{2,3}\b", text))
        has_numbers = bool(re.search(r"\d+", text))

        if has_weight:
            markers.append("weight_measurement")
        if has_bp:
            markers.append("blood_pressure")

        # 2. Negations (Critical to preserve clinical intent: absence of disease / refusal)
        negation_pattern = r"\b(ಇಲ್ಲ|ಆಗಿಲ್ಲ|ಇಲ್ಲವೇ ಇಲ್ಲ|ಬೇಡ|no|not|none|negative|absent|nahi|नहीं|ना)\b"
        has_negation = bool(re.search(negation_pattern, text, re.IGNORECASE))
        if has_negation:
            markers.append("explicit_negation")

        # 3. Key Vaccines
        for v in ["BCG", "OPV", "Penta", "Rotavirus", "PCV", "MR", "DPT", "Td", "Vitamin A"]:
            if re.search(rf"\b{v}\b", text, re.IGNORECASE):
                markers.append(f"vaccine:{v}")

        return {
            "has_numbers": has_numbers,
            "has_weight": has_weight,
            "has_bp": has_bp,
            "has_negation": has_negation,
            "detected_markers": markers
        }

    @staticmethod
    def format_phase2_payload(transcript: str, language_code: str, status: str = "completed") -> Dict[str, Any]:
        """
        Formats transcript to the common Phase 2 JSON contract with full audit trail:
        {
          "transcript": "The baby weight is 3.2 kg and OPV-1 is due.",
          "language": "kn-en",
          "status": "completed"
        }
        Preserves original raw transcript in 'raw_transcript' and normalized in 'normalized_transcript'.
        Never invents text if transcript is empty.
        """
        raw = transcript.strip()
        normalized, corrections = AudioProcessor.apply_verified_medical_normalization(raw)
        clinical_markers = AudioProcessor.detect_clinical_markers(normalized if normalized else raw)

        # Primary transcript is normalized (preserving Phase 2 contract), with raw preserved
        primary_transcript = normalized if normalized else raw

        return {
            "transcript": primary_transcript,
            "raw_transcript": raw,
            "normalized_transcript": normalized,
            "corrections_applied": corrections,
            "clinical_markers": clinical_markers,
            "language": AudioProcessor.map_language_to_phase2(language_code),
            "status": status
        }
