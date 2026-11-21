# ASHA SAHAYAK (आशा सहायक / ಆಶಾ ಸಹಾಯಕ)
> **Integrated AI-Powered Voice Field Register and Healthcare Management System**

---

## 📌 Project Overview

**ASHA SAHAYAK** is an intelligent, voice-first digital field register and clinical safety assistant designed to empower Accredited Social Health Activists (ASHA workers) and Primary Health Centres (PHCs) across rural and urban India.

During household maternal and child health visits, ASHA workers speak naturally in their native language (e.g., Kannada, Hindi, Indian English, or code-mixed dialects). The platform captures real-time speech, performs streaming transcription, extracts structured clinical visit data, screens for critical maternal and newborn danger signs according to public health protocols, conducts voice read-backs for verification, allows natural voice corrections, and synchronizes confirmed records with the SQLite health register.

---

## 🌟 End-to-End System Architecture

```
[Browser Mic (ASHA Worker)]
          │ (Web Audio API: 16kHz Linear PCM downsampled, Float32 -> Int16)
          ▼
[React Frontend (VoiceRecorder.jsx / StructuredVisitReport.jsx)]
          │ (Binary WebSocket streaming: /api/voice/stream, /ws/audio)
          ▼
[FastAPI Backend (backend/main.py)]
          │
          ├─── Phase 1: Voice Input & Synthesis Engine
          │     ├── [AudioProcessor]: RMS level, silence check, 10-language code mapping
          │     ├── [Gnani Prisma v3.0 STT]: Streaming raw 16-bit PCM mono frames
          │     ├── [Gnani Timbre TTS]: Natural voice synthesis for readbacks
          │     ├── [Medical Vocabulary]: 200+ medical keyterms & UIP vaccine boosting
          │     └── [MockTranscriptionEngine]: Resilient offline fallback
          │
          ├─── Phase 2: AI Understanding & Safety Engine
          │     ├── [Qwen / Rule Extraction]: Structured field extraction (ANC, PNC, HBNC)
          │     ├── [MoHFW / IMNCI Safety Rules]: Instant screening of maternal & infant danger signs
          │     ├── [Negation Handling]: Distinguishes "no fever" / "bleeding illa" from positive symptoms
          │     ├── [Voice Read-Back & Corrections]: Iterative voice adjustments before confirmation
          │     └── [Safe Referral Advisor]: Structured PHC/CHC/FRU referral advisories
          │
          └─── Phase 3: Field Register & Community Health Management
                ├── [POST /api/visits/confirm]: Enforces confirmation status barrier
                ├── [SHA-256 Deduplication]: Deterministic checksum duplicate prevention
                ├── [Safe Follow-ups]: Null-date preservation (no invented dates)
                ├── [SQLite Database]: Thread-safe Write-Ahead Logging (WAL) & foreign keys
                ├── [Role-Based Access Control]: Admin, ASHA Worker, Health Supervisor
                ├── [Geographical Scoping]: State, District, Taluk, Village & PIN code scoping
                ├── [Household Surveys]: Member profiling (pregnant, child <5 immunization, elderly)
                └── [ASHA Worker Finder]: Public locator by PIN code, village, or GPS (/api/workers/find)
```

---

## 📋 Phase 2 to Phase 3 Interface Contract

### Endpoint: `POST /api/visits/confirm`

The Phase 3 backend receives and validates the worker-confirmed structured visit record produced by Phase 2:

```json
{
  "beneficiary_id": "BNF-2041",
  "visit_type": "Newborn home visit",
  "weight": "3.2 kg",
  "vaccinations_due": [
    "OPV-1"
  ],
  "next_visit_date": null,
  "danger_signs": [],
  "referral_required": false,
  "confirmation_status": "confirmed"
}
```

### Invariants & Validation Rules:
1. **Explicit Confirmation Enforcement:**
   - Only records with `"confirmation_status": "confirmed"` are persisted to the SQLite register.
   - Any unconfirmed, pending, or missing confirmation returns **`HTTP 400 Bad Request`**.
2. **Duplicate Prevention (SHA-256 Checksum):**
   - A deterministic hash is computed across `beneficiary_id + visit_type + visit_date + weight + vaccinations_due`.
   - Repeated submissions return **`HTTP 409 Conflict`** with the matching fingerprint.
3. **Follow-Up Date Integrity (No Fabrication):**
   - If `next_visit_date` is `null` (e.g., newborn BNF-2041), the system **does not invent a follow-up date**.
   - If a date is provided (e.g., `"2026-12-05"`), an upcoming follow-up record is scheduled.
4. **Referral Alerts without Algorithmic Diagnosis:**
   - If `referral_required` is `true` or `danger_signs` are observed, an alert is surfaced for the Medical Officer at the PHC. The system retains clinical observations without making independent diagnoses.

---

## 👥 Role-Based Access Control Demo Logins

| Role | Username | Password | Coverage Scoping |
|------|----------|----------|-------------------|
| **ASHA Worker (Rampur Sector 1)** | `asha_rampur` | `asha123` | Village: Rampur, PIN: `571428` |
| **ASHA Worker (Rampur Sector 2)** | `asha_rampur_2` | `asha123` | Village: Rampur, PIN: `571428` |
| **ASHA Worker (Kalyanpur)** | `asha_kalyanpur` | `asha123` | Village: Kalyanpur, PIN: `571434` |
| **Taluk Health Supervisor** | `supervisor_maddur` | `sup123` | Taluk: Maddur, Subcenters & Surveys |
| **Medical Officer / Administrator** | `admin` | `admin123` | Global system access across all areas |

---

## 🚀 How to Run the Integrated Application

### 1. Start the Shared FastAPI Backend Server
```powershell
cd "c:\Users\manju\Asha Sahayak\Asha-Sahayak"
& "C:\Users\manju\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access the Application in Your Browser
- **Unified Web Application:** [http://localhost:8000/](http://localhost:8000/)
- **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Live WebSocket Audio Endpoint:** `ws://localhost:8000/api/voice/stream` or `ws://localhost:8000/ws/audio`
- **System Health Status:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 3. (Optional) Run Vite Frontend in Development Mode
```powershell
cd "c:\Users\manju\Asha Sahayak\Asha-Sahayak\frontend"
& "C:\Program Files\nodejs\npm.cmd" run dev
```

---

## 🧪 Verification & Automated Test Suites

```powershell
cd "c:\Users\manju\Asha Sahayak\Asha-Sahayak"

# 1. Run all pytest test suites
& "C:\Users\manju\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests/ -v

# 2. Run Location-Based ASHA Worker Finder verification (10 Scenarios)
& "C:\Users\manju\AppData\Local\Programs\Python\Python312\python.exe" tests/test_finder_portal.py
```
*(All 20+ automated tests passing with 100% success)*
