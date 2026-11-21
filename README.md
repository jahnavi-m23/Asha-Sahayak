# ASHA SAHAYAK (ಆಶಾ ಸಹಾಯಕ)
> **AI-Powered Voice-Based Field Register for ASHA Workers**

---

## 📌 Project Overview

**ASHA SAHAYAK** is an intelligent, voice-first digital assistant and field register designed to empower Accredited Social Health Activists (ASHA workers) across rural and urban India. During household maternal and child health visits, ASHA workers can simply speak naturally in their native language (e.g., Kannada, Hindi, English, or code-mixed dialects). The platform captures real-time speech, performs streaming transcription, extracts structured clinical visit data, screens for critical maternal and newborn danger signs according to public health protocols, conducts voice read-backs for verification, allows natural voice corrections, and synchronizes confirmed records with the health register.

---

## 🚀 Key Features

### Phase 1: Voice Input & Speech Synthesis
- **Streaming Speech-to-Text (STT)**: High-accuracy real-time speech recognition powered by Gnani Prisma v3.0 over WebSockets.
- **10 Supported Indian Languages**: Kannada, Hindi, Indian English, Tamil, Telugu, Malayalam, Marathi, Bengali, Gujarati, and Punjabi.
- **Automatic Language Detection (`indic-auto`)**: Automatically identifies spoken languages without manual switching.
- **Code-Mixing Support**: Accurately recognizes blended dialects such as Kannada-English (`kn-IN,en-IN`) and Hindi-English (`hi-IN,en-IN`).
- **Text-to-Speech (TTS)**: Natural voice read-backs using Gnani Timbre with locale-matched regional voices (e.g., Devika, Nalini, Kaveri).
- **Client-Side Audio Downsampling**: Web Audio API downsamples raw mic input to 16 kHz 16-bit PCM mono with RMS silence detection.
- **Graceful Mock Fallback**: Automatic mock engines when offline or without external credentials.

### Phase 2: AI Understanding, Data Extraction and Safety
- **Structured Clinical Extraction**: Automatically extracts maternal and child health fields (beneficiary name, gestational age, infant weight, blood pressure, vaccinations, reported symptoms).
- **Public Health Guidelines**: Clinical safety rules aligned with Ministry of Health and Family Welfare (**MoHFW**) Home Based Newborn Care (HBNC), Antenatal Care (ANC), and WHO/UNICEF **IMNCI** protocols.
- **Danger-Sign Detection**: Instant identification of red-flag symptoms (severe headache, blurred vision, convulsions, vaginal bleeding, infant hypothermia, fever, respiratory distress).
- **Negation & Context Awareness**: Distinguishes actual symptoms from negated reports ("no fever", "ಜ್ವರ ಇಲ್ಲ", "bleeding illa") to avoid false alarms.
- **Voice Read-Back & Iterative Corrections**: Confirms extracted data with the worker via voice read-back and allows targeted voice updates (e.g., "No, weight is 2.8 kg").
- **Zero Hallucination & Safe Referral**: Never invents unmentioned clinical details or prescribes medication; generates structured PHC/CHC/FRU referral advisories.

### Phase 3: Field Register & Dashboard
- **Structured Visit Records**: Persistent visit ledger storing confirmed health visit reports.
- **Follow-up & Schedule Tracking**: Next visit dates, due immunizations (OPV, BCG, Pentavalent, Td), and high-risk case flags.
- **Interactive UI**: Responsive React + Vite dashboard displaying visit histories and audio controls.

---

## 🏗️ Architecture & Data Flow

```
[Browser Mic (ASHA Worker)]
          │ (Web Audio API: 16kHz Linear PCM downsampled, Float32 -> Int16)
          ▼
[React Frontend (VoiceRecorder.jsx / StructuredVisitReport.jsx)]
          │ (Binary WebSocket streaming / REST API)
          ▼
[FastAPI Backend (backend/main.py)]
          │
          ├─── Phase 1: Voice Engine
          │     ├── [AudioProcessor]: RMS level, silence check, 10-language code mapping
          │     ├── [Gnani Prisma v3.0 STT]: Streaming raw 16-bit PCM mono frames
          │     ├── [Gnani Timbre TTS]: Natural voice synthesis for readbacks
          │     └── [MockTranscriptionEngine]: Resilient offline fallback
          │
          ├─── Phase 2: AI & Safety Engine
          │     ├── [Medical Vocabulary]: 200+ medical terms and UIP vaccine catalog
          │     ├── [Rule & Qwen Extractors]: Clinical field extraction & normalization
          │     ├── [DangerSignDetector]: Negation-aware MoHFW / IMNCI safety rules
          │     ├── [VoiceCorrectionHandler]: Single-field updates with state preservation
          │     └── [VoiceReadbackService]: Multilingual audio confirmation generation
          │
          └─── Phase 3: Field Register & Handoff
                ├── [Register Store]: In-memory & database visit records
                └── [Phase3Client]: Common JSON handoff contracts
```

---

## 🌐 Supported Indian Languages

| Locale Code | Language | Native Name | STT (Prisma v3.0) | TTS (Timbre Default Voice) | Available Voices |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `kn-IN` | Kannada | ಕನ್ನಡ | Supported | `Devika` | `Devika`, `Nayana`, `Girish`, `Pranav` |
| `hi-IN` | Hindi | हिन्दी | Supported | `Nalini` | `Nalini`, `Deepak` |
| `en-IN` | Indian English | English (India) | Supported | `Kaveri` | `Kaveri`, `Pranav` |
| `ta-IN` | Tamil | தமிழ் | Supported | `Oviya` | `Oviya`, `Kavin` |
| `te-IN` | Telugu | తెలుగు | Supported | `Devika` | `Devika`, `Chitra`, `Pranav` |
| `ml-IN` | Malayalam | മലയാളം | Supported | `Devika` | `Devika`, `Radhika` |
| `mr-IN` | Marathi | मराठी | Supported | `Madhuri` | `Madhuri`, `Radhika`, `Omkar` |
| `bn-IN` | Bengali | বাংলা | Supported | `Eishani` | `Eishani`, `Tanvi` |
| `gu-IN` | Gujarati | ગુજરાતી | Supported | `Falguni` | `Falguni`, `Chirag` |
| `pa-IN` | Punjabi | ਪੰਜਾਬੀ | Supported | `Kartik` | `Kartik`, `Devika` |

**Special STT Modes**:
- `indic-auto`: Gnani Prisma automatic language detection across all 10 Indian languages.
- `kn-IN,en-IN`: Kannada + English code-mixed recognition.
- `hi-IN,en-IN`: Hindi + English code-mixed recognition.

---

## 📂 Project Structure

```
Asha-Sahayak/
├── backend/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── medical_vocab.py       # Kannada-English medical terms & UIP vaccine dictionary
│   │   ├── transcript_parser.py   # Regex parsing (measurements, dates, Kannada numerals)
│   │   ├── rule_extractor.py      # Python Rule-Based Extraction Engine (Zero Qwen dependency)
│   │   ├── qwen_extractor.py      # Modular Qwen LLM extractor (when API key is provided)
│   │   ├── voice_readback.py      # Gnani Timbre TTS voice synthesis service
│   │   ├── voice_corrector.py     # Iterative voice correction handler
│   │   └── phase3_client.py       # Handoff client formatting records for Phase 3
│   ├── extraction/
│   │   ├── __init__.py
│   │   └── engine.py              # ASHA extraction engine utilities
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic v2 schemas and data contracts
│   ├── routes/
│   │   ├── __init__.py            # Central route exports (ai_router, voice_router, report_router)
│   │   ├── ai.py                  # Phase 2 REST & WebSocket endpoints (/api/ai)
│   │   ├── report.py              # Phase 3 Register & extraction endpoints (/api/report)
│   │   └── voice.py               # Phase 1 Voice STT, TTS & WebSocket endpoints (/api/voice)
│   ├── safety/
│   │   ├── __init__.py
│   │   ├── guidelines.py          # Clinical rules with MoHFW HBNC, ANC, and IMNCI citations
│   │   ├── danger_signs.py        # Detector with negation and hypothetical filters
│   │   └── referral_advisor.py    # Localized urgent PHC/FRU referral generator
│   ├── translation/
│   │   ├── __init__.py
│   │   └── engine.py              # Multilingual translation engine (IndicTrans2 / Bhashini)
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── audio_processor.py     # PCM audio validation, RMS calculations & downsampling
│   │   ├── config.py              # Voice configuration and language mappings
│   │   ├── gnani_client.py        # Gnani Prisma v3.0 WebSocket STT client
│   │   ├── gnani_tts_client.py    # Gnani Timbre TTS REST client
│   │   ├── medical_vocabulary.py  # Phonetic corrections & medical dictionary
│   │   ├── mock_engine.py         # Resilient mock transcription and synthesis fallbacks
│   │   └── wer_evaluator.py       # Word Error Rate (WER) evaluation utility
│   ├── tests/                     # Phase 1 & integration tests
│   ├── config.py                  # Pydantic BaseSettings application configuration
│   ├── main.py                    # Unified FastAPI application instance with all routers
│   └── requirements.txt           # Backend Python dependencies
├── frontend/                      # React + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Phase3Dashboard.jsx        # Field register dashboard & statistics
│   │   │   ├── StructuredVisitReport.jsx  # Structured report display & review
│   │   │   └── VoiceRecorder.jsx          # Live microphone streaming component
│   │   ├── utils/
│   │   │   └── audioUtils.js              # Audio downsampling and PCM conversion
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── tests/                         # Phase 2 unit & endpoint tests
├── .env.example                   # Environment variable templates
└── README.md                      # Comprehensive project documentation
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- **Python**: 3.10+ (Tested on Python 3.14)
- **Node.js**: 18+ and npm
- **Microphone**: Enabled in browser for voice recording

### 2. Backend Setup
```bash
# Navigate to project root
cd Asha-Sahayak

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp backend/.env.example backend/.env
# or copy to root:
cp backend/.env.example .env
```

Configure your environment variables in `.env` (do not commit this file):

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `GNANI_API_KEY` | API Key for Gnani Prisma STT & Timbre TTS | *(Leave empty for mock mode)* |
| `GNANI_WEBSOCKET_URL` | WebSocket endpoint for Gnani Prisma v3.0 STT | `wss://api.vachana.ai/stt/v3/stream` |
| `GNANI_MODEL` | Gnani STT model identifier | `prisma-v3.0` |
| `GNANI_DEFAULT_LANGUAGE` | Default STT language code | `indic-auto` |
| `GNANI_TTS_URL` | Endpoint for Gnani Timbre TTS | `https://api.vachana.ai/api/v1/tts/inference` |
| `GNANI_TTS_MODEL` | Gnani TTS model identifier | `timbre-v2.5` |
| `GNANI_TTS_DEFAULT_VOICE`| Default voice for readbacks | `Devika` |
| `QWEN_API_KEY` | Optional API Key for Qwen LLM | *(Optional; rule engine used by default)* |
| `QWEN_API_BASE` | Base URL for Qwen OpenAI-compatible API | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| `QWEN_MODEL_NAME` | Model name for Qwen | `qwen-plus` |
| `ALLOW_MOCK_FALLBACK` | Allow offline heuristic and mock audio fallback | `true` |
| `BACKEND_HOST` | FastAPI server host | `0.0.0.0` |
| `BACKEND_PORT` | FastAPI server port | `8000` |
| `CORS_ORIGINS` | Permitted CORS origins | `http://localhost:3000,http://localhost:5173` |

### 4. Running the Backend Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
The unified FastAPI documentation is available at `http://localhost:8000/docs`.

### 5. Frontend Setup
```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 📡 API Reference & Endpoints

### Phase 1: Voice Recognition & Synthesis (`/api/voice`)
- `WebSocket /api/voice/stream`: Live PCM binary audio streaming for real-time speech recognition.
- `GET /api/voice/status`: Check Gnani credentials and STT engine status.
- `GET /api/voice/languages`: List all 10 supported Indian languages and voices.
- `POST /api/voice/synthesize`: Synthesize text to speech using Gnani Timbre.
- `POST /api/voice/translate`: Translate transcripts between supported Indian languages.
- `GET /api/voice/recent`: Retrieve recent speech recognition transcripts.

### Phase 2: AI Understanding & Clinical Safety (`/api/ai`)
- `POST /api/ai/process-transcript`: Process raw transcripts to extract structured visit fields, evaluate danger signs, and generate voice read-back audio.
- `POST /api/ai/correct-record`: Perform targeted single-field voice corrections while preserving unaffected fields.
- `POST /api/ai/confirm-record`: Mark records as verified by the ASHA worker and hand off to Phase 3.
- `POST /api/ai/synthesize-speech`: Synthesize localized readback speech.
- `GET /api/ai/danger-signs/rules`: View active clinical danger sign definitions and guideline citations.
- `GET /api/ai/health`: Health status of AI extraction and safety rules.
- `WebSocket /api/ai/ws/interaction`: Interactive bidirectional conversational WebSocket.

### Phase 3: Field Register (`/api/report`)
- `POST /api/report/extract`: Direct extraction of visit report from text.
- `POST /api/report/save`: Persist confirmed visit report into the register.
- `GET /api/report/list`: List all recorded beneficiary visits.
- `GET /api/report/{record_id}`: Retrieve a specific visit report.
- `DELETE /api/report/{record_id}`: Remove a visit report.
- `GET /api/report/stats/summary`: Aggregate statistics on visits, danger signs, and referrals.

---

## 🛡️ Public Health Safety & Danger Signs Matrix

| Code | Danger Sign | Category | Guidelines Citation | Action / Referral Protocol |
| :--- | :--- | :--- | :--- | :--- |
| `HBNC-DS-01` | High fever in newborn (> 38°C) | Newborn | MoHFW HBNC Guidelines & WHO/UNICEF IMNCI | Urgent referral to PHC/CHC. Keep baby warm. |
| `HBNC-DS-02` | Hypothermia (< 35.5°C) | Newborn | MoHFW HBNC Module 3 | Provide Kangaroo Mother Care; emergency transport to PHC/FRU. |
| `HBNC-DS-03` | Inability to feed / suckle | Newborn | WHO/UNICEF IMNCI Protocols | Critical danger sign; emergency transport to PHC/FRU. |
| `HBNC-DS-04` | Convulsions / Fits / Tremors | Newborn | MoHFW HBNC Manual & IMNCI | Critical emergency; clear airway, rush to FRU/District Hospital. |
| `HBNC-DS-05` | Fast breathing / Chest indrawing | Newborn | MoHFW HBNC Respiratory Distress Protocols | Urgent referral to PHC/CHC equipped with oxygen support. |
| `HBNC-DS-06` | Severe Jaundice (Day 1 / Palms / Soles) | Newborn | MoHFW HBNC Neonatal Jaundice Protocol | Refer to PHC for phototherapy and bilirubin evaluation. |
| `HBNC-DS-07` | Umbilical sepsis / Pus discharge | Newborn | MoHFW HBNC Umbilical Sepsis Guidelines | High priority; keep dry, do not apply home remedies, refer to PHC. |
| `ANC-DS-01` | Vaginal bleeding in pregnancy (APH) | Pregnancy | MoHFW Antenatal Care (ANC) Guidelines | Critical emergency; arrange 108 Ambulance immediately to FRU. |
| `ANC-DS-02` | Severe headache + blurred vision / High BP | Pregnancy | MoHFW ANC Guidelines: Pre-eclampsia | Critical emergency; refer immediately to FRU/CHC. |
| `ANC-DS-03` | Eclampsia / Convulsions in pregnancy | Pregnancy | MoHFW Emergency Obstetric Care (EmOC) | Left lateral position, clear airway, rush to FRU via 108 Ambulance. |
| `PNC-DS-01` | Postpartum Hemorrhage (PPH) | Postpartum | MoHFW Postnatal Care & PPH Management | Critical emergency; urgent transport to FRU. |
| `PNC-DS-02` | Foul-smelling lochia / Puerperal sepsis | Postpartum | MoHFW Postnatal Care Manual | Urgent evaluation at PHC for puerperal sepsis. |

### Strict Public Health Rules Enforced
1. **Zero Hallucination**: Never invent missing beneficiary IDs, dates, weights, or vaccines. Missing items are set to `null` and listed in `missing_fields`.
2. **No Medical Prescription**: Never prescribe medications, suggest drugs (e.g., paracetamol, antibiotics), or specify dosages.
3. **No Clinical Diagnosis**: Never declare clinical disease diagnoses; prompt immediate transfer to authorized public health centers (PHC, CHC, FRU).
4. **Context & Negation Checking**: Statements like "no fever", "ಜ್ವರ ಇಲ್ಲ", "bleeding illa", or conditional advice ("if fever occurs...") do not trigger false positive emergency alerts.

---

## 🧪 Running Automated Tests

Run the full pytest suite for both Phase 1 and Phase 2:
```bash
# Run all tests
pytest tests backend/tests -v
```

- `tests/`: Covers Phase 2 structured entity extraction, zero hallucination, danger signs detection, negation filtering, voice correction loops, voice readback synthesis, and FastAPI endpoint tests.
- `backend/tests/`: Covers Phase 1 10-language PCM streaming audio, Gnani Prisma STT, Gnani Timbre TTS, translation, WER accuracy, and end-to-end report workflow tests.
