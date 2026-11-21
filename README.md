# ASHA SAHAYAK (ಆಶಾ ಸಹಾಯಕ)

AI-Powered Voice-Based Field Register for ASHA Workers.

---

## Phase 1: Voice Input (STT) & Speech Synthesis (TTS)

Phase 1 provides real-time voice capture, streaming speech recognition, and speech synthesis designed for ASHA workers during household visits across India.

### 10 Supported Indian Languages (Gnani Documented)

| Locale Code | Language | Native Name | STT (Prisma v3.0) | TTS (Timbre v2.5 Default Voice) | Available Voices |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `kn-IN` | Kannada | ಕನ್ನಡ | Supported | `Kavya` | `Kavya`, `Pranav` |
| `hi-IN` | Hindi | हिन्दी | Supported | `Nalini` | `Nalini`, `Deepak` |
| `en-IN` | Indian English | English (India) | Supported | `Kaveri` | `Kaveri`, `Pranav` |
| `ta-IN` | Tamil | தமிழ் | Supported | `Amala` | `Amala`, `Murugan` |
| `te-IN` | Telugu | తెలుగు | Supported | `Swathi` | `Swathi`, `Kiran` |
| `ml-IN` | Malayalam | മലയാളം | Supported | `Anitha` | `Anitha`, `Rahul` |
| `mr-IN` | Marathi | मराठी | Supported | `Shubhra` | `Shubhra`, `Kunal` |
| `bn-IN` | Bengali | বাংলা | Supported | `Mithila` | `Mithila`, `Debjit` |
| `gu-IN` | Gujarati | ગુજરાતી | Supported | `Kinjal` | `Kinjal`, `Jignesh` |
| `pa-IN` | Punjabi | ਪੰਜਾਬੀ | Supported | `Simran` | `Simran`, `Harpreet` |

#### Additional STT Modes:
- **Automatic Language Detection (`indic-auto`):** Dynamically identifies the spoken Indian language from the 10 supported locales.
- **Code-Mixing:** Supports `kn-IN,en-IN` (Kannada + English) and `hi-IN,en-IN` (Hindi + English).

---

### Architecture Overview

```
[Browser Mic (ASHA Worker)]
          │ (Web Audio API: 16kHz Linear PCM downsampled, Float32 -> Int16)
          ▼
[React Frontend (VoiceRecorder.jsx)]
          │ (Binary WebSocket streaming)
          ▼
[FastAPI Backend (/api/voice/stream)]
          │
          ├─── [AudioProcessor]: RMS level, silence check, 10-language Phase 2 code mapping
          │
          ├─── [Gnani Prisma v3.0 STT Client] (wss://api.vachana.ai/stt/v3/stream)
          │         └── Streaming raw 16-bit PCM mono frames
          │         └── Headers: X-API-Key-ID, model=prisma-v3.0, language_code (or indic-auto)
          │
          ├─── [Gnani Timbre v2.5 TTS Client] (https://api.vachana.ai/api/v1/tts/inference)
          │         └── Synthesizes speech confirmation in user's preferred language/voice
          │
          └─── [MockTranscriptionEngine & Mock TTS] (Labeled fallback when credentials are absent)
          │
          ▼
[Phase 2 Handoff JSON Contract]
{
  "transcript": "The baby weight is 3.2 kg and OPV-1 is due.",
  "language": "kn-en",
  "status": "completed"
}
```

---

### Setup Instructions

#### 1. Backend Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Store your Gnani API Key in `backend/.env`:
   ```env
   GNANI_API_KEY=your_gnani_api_key_here
   GNANI_WEBSOCKET_URL=wss://api.vachana.ai/stt/v3/stream
   GNANI_MODEL=prisma-v3.0
   GNANI_DEFAULT_LANGUAGE=indic-auto

   GNANI_TTS_URL=https://api.vachana.ai/api/v1/tts/inference
   GNANI_TTS_MODEL=timbre-v2.5
   GNANI_TTS_DEFAULT_VOICE=Kavya
   GNANI_TTS_DEFAULT_LANGUAGE=kn-IN
   ```
   *(If `GNANI_API_KEY` is not provided, the backend runs in clearly labeled `[MOCK FALLBACK]` mode for both STT and TTS).*

3. Run the FastAPI server:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### 2. Frontend Configuration

1. Install and start:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Open `http://localhost:5173`.

---

### Running Automated Tests

Run the full pytest suite:
```bash
pytest backend/tests -v
```

All 9 test cases covering 10-language validation, PCM downsampling, Phase 2 contracts, Timbre v2.5 synthesis, and Prisma v3.0 WebSocket auto-detection pass in under 1 second.
