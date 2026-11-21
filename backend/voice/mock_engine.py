from typing import Dict, Any, List, Tuple
from backend.voice.config import SUPPORTED_LANGUAGES

class MockTranscriptionEngine:
    """
    SIMULATION / FALLBACK ENGINE.
    Active ONLY in offline development when GNANI_API_KEY is not configured.
    CRITICAL RULE:
    Never generates simulated transcripts from silent audio buffers.
    Only simulates speech if actual speech energy was detected.
    """

    MOCK_SCENARIOS: Dict[str, List[Tuple[str, bool]]] = {
        "hi-in": [
            ("बच्चे का वजन...", False),
            ("बच्चे का वजन 3.2 किलोग्राम है...", False),
            ("बच्चे का वजन 3.2 किलोग्राम है और OPV-1 टीका दिया गया है।", True)
        ],
        "kn-in": [
            ("ಮಗುವಿನ ತೂಕ...", False),
            ("ಮಗುವಿನ ತೂಕ 3.2 ಕೆಜಿ...", False),
            ("ಮಗುವಿನ ತೂಕ 3.2 ಕೆಜಿ ಮತ್ತು OPV-1 ಲಸಿಕೆ ನೀಡಲಾಗಿದೆ.", True)
        ],
        "en-in": [
            ("The baby weight...", False),
            ("The baby weight is 3.2 kg...", False),
            ("The baby weight is 3.2 kg and OPV-1 is due.", True)
        ],
        "ta-in": [
            ("குழந்தையின் எடை...", False),
            ("குழந்தையின் எடை 3.2 கிலோ...", False),
            ("குழந்தையின் எடை 3.2 கிலோ மற்றும் OPV-1 தடுப்பூசி செலுத்தப்பட்டது.", True)
        ],
        "te-in": [
            ("శిశువు బరువు...", False),
            ("శిశువు బరువు 3.2 కిలోలు...", False),
            ("శిశువు బరువు 3.2 కిలోలు ಮತ್ತು OPV-1 టీకా ఇవ్వబడింది.", True)
        ],
        "ml-in": [
            ("കുഞ്ഞിന്റെ ഭാരം...", False),
            ("കുഞ്ഞിന്റെ ഭാരം 3.2 കിലോഗ്രാം...", False),
            ("കുഞ്ഞിന്റെ ഭാരം 3.2 കിലോഗ്രാം ആണ്, OPV-1 വാക്സിൻ നൽകി.", True)
        ],
        "mr-in": [
            ("बाळाचे वजन...", False),
            ("बाळाचे वजन 3.2 किलो आहे...", False),
            ("बाळाचे वजन 3.2 किलो आहे आणि OPV-1 लस दिली आहे.", True)
        ],
        "bn-in": [
            ("শিশুর ওজন...", False),
            ("শিশুর ওজন 3.2 কেজি...", False),
            ("শিশুর ওজন 3.2 কেজি এবং OPV-1 টিকা দেওয়া হয়েছে।", True)
        ],
        "gu-in": [
            ("બાળકનું વજન...", False),
            ("બાળકનું વજન 3.2 કિગ્રા છે...", False),
            ("બાળકનું વજન 3.2 કિગ્રા છે અને OPV-1 રસી આપવામાં આવી છે.", True)
        ],
        "pa-in": [
            ("ਬੱਚੇ ਦਾ ਭਾਰ...", False),
            ("ਬੱਚੇ ਦਾ ਭਾਰ 3.2 ਕਿਲੋਗ੍ਰਾਮ ਹੈ...", False),
            ("ਬੱਚੇ ਦਾ ਭਾਰ 3.2 ਕਿਲੋਗ੍ਰਾਮ ਹੈ ਅਤੇ OPV-1 ਟੀਕਾ ਲਗਾਇਆ ਗਿਆ ਹੈ।", True)
        ],
        "kn-en": [
            ("ಮಗುವಿನ weight 3.2 kg...", False),
            ("ಮಗುವಿನ weight 3.2 kg ಇದೆ, OPV-1 vaccine due...", False),
            ("ಮಗುವಿನ weight 3.2 kg ಇದೆ, ಮತ್ತು OPV-1 vaccine due ಆಗಿದೆ, BP 120/80 normal ಇದೆ.", True)
        ],
        "hi-en": [
            ("Baby ka weight...", False),
            ("Baby ka weight 3.2 kg hai, OPV-1 due...", False),
            ("Baby ka weight 3.2 kg hai, aur OPV-1 vaccine due hai, BP 120/80 normal hai.", True)
        ]
    }

    def __init__(self, language_code: str = "indic-auto"):
        self.language_code = language_code.lower().strip()
        self.key = self._resolve_scenario_key(self.language_code)
        self.step = 0
        self.received_audio_bytes = 0
        self.speech_chunks_count = 0
        self.silent_chunks_count = 0

    def _resolve_scenario_key(self, lang: str) -> str:
        if "indic-auto" in lang or lang == "auto":
            return "kn-en"
        if "kn" in lang and "en" in lang:
            return "kn-en"
        if "hi" in lang and "en" in lang:
            return "hi-en"
        for code in self.MOCK_SCENARIOS.keys():
            if code in lang or lang.replace("-", "").startswith(code.replace("-", "")):
                return code
        return "kn-en"

    def register_audio_chunk(self, chunk_len: int, is_speech: bool = False):
        self.received_audio_bytes += chunk_len
        if is_speech:
            self.speech_chunks_count += 1
        else:
            self.silent_chunks_count += 1

    def has_detected_speech(self) -> bool:
        return self.speech_chunks_count >= 2

    def should_generate_event(self) -> bool:
        """Only generate mock event if genuine speech energy was detected in the buffer."""
        return self.has_detected_speech()

    async def generate_mock_event(self) -> Dict[str, Any]:
        """Simulates periodic recognition ONLY when speech is present."""
        if not self.has_detected_speech():
            return {
                "type": "silence",
                "transcript": "",
                "is_final": False,
                "is_mock": True,
                "is_simulation": True,
                "engine": "mock_simulation"
            }

        scenario = self.MOCK_SCENARIOS.get(self.key, self.MOCK_SCENARIOS["kn-en"])
        
        if self.step < len(scenario):
            transcript_text, is_final = scenario[self.step]
            self.step += 1
        else:
            transcript_text, is_final = scenario[-1]

        detected_lang = self.key.replace("-", "-IN").upper() if "-in" in self.key else self.language_code

        return {
            "type": "transcript",
            "transcript": f"[SIMULATION] {transcript_text}",
            "is_final": is_final,
            "confidence": 0.95,
            "language_code": self.language_code,
            "detected_language_code": detected_lang,
            "is_mock": True,
            "is_simulation": True,
            "engine": "mock_simulation",
            "mock_notice": "⚠️ SIMULATION FALLBACK: Real Gnani API credentials are not configured in backend/.env"
        }

    def get_final_payload(self) -> Dict[str, Any]:
        """Returns final payload. If no speech was detected, returns empty transcript."""
        if not self.has_detected_speech():
            return {
                "transcript": "",
                "language": self.key,
                "status": "completed",
                "is_mock": True,
                "is_simulation": True,
                "engine": "mock_simulation",
                "speech_detected": False,
                "message": "No speech detected in audio."
            }

        scenario = self.MOCK_SCENARIOS.get(self.key, self.MOCK_SCENARIOS["kn-en"])
        final_text = scenario[-1][0]
        return {
            "transcript": f"[SIMULATION] {final_text}",
            "language": self.key,
            "status": "completed",
            "is_mock": True,
            "is_simulation": True,
            "engine": "mock_simulation",
            "speech_detected": True
        }
