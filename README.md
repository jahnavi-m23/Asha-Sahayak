# ASHA SAHAYAK (आशा सहायक / ಆಶಾ ಸಹಾಯಕ)
### Integrated AI-Powered Voice Field Register and Healthcare Management System

**ASHA Sahayak** is a mission-critical digital assistant for Accredited Social Health Activists (ASHA workers) and Primary Health Centres (PHCs). It replaces paper-based registers with a voice-first clinical recording workflow, automated entity extraction, robust database persistence, and community health monitoring.

---

## 🌟 End-to-End System Architecture

```
+-----------------------------------------------------------------------------------+
|                        PHASE 1: VOICE RECOGNITION MODULE                          |
|  - Real-time field audio streaming via WebSocket (/ws/audio)                     |
|  - Multilingual Speech-to-Text (Kannada kn-IN, Hindi hi-IN, English en-IN)       |
|  - Domain vocabulary normalization (vaccines, ANC/PNC visits, danger signs)      |
+-----------------------------------------+-----------------------------------------+
                                          |
                              Voice Transcript / Audio Chunks
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        PHASE 2: AI CLINICAL EXTRACTION                            |
|  - Clinical entity extraction from field voice notes                              |
|  - Structured visit JSON generation                                               |
|  - Pre-confirmation review card: Worker verifies weight, vaccine & referral      |
+-----------------------------------------+-----------------------------------------+
                                          |
                          POST /api/visits/confirm (Status: "confirmed")
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                 PHASE 3: DATABASE, DASHBOARD & FOLLOW-UP MANAGEMENT                |
|  - SQLite Database with Write-Ahead Logging (WAL) and Foreign Keys                |
|  - SHA-256 Checksum Duplicate Visit Prevention (HTTP 409 Conflict)                |
|  - Safe Follow-up Scheduling (Strictly preserves null - No date fabrication)      |
|  - PHC Emergency Referral Flagging with Danger Signs Retention                    |
|  - Role-Based Access Control (Administrator, ASHA Worker, Health Supervisor)      |
|  - Geographical Area & Postal PIN Code Scoping (Mandya / Maddur / Rampur)         |
|  - Household & Family Health Survey with Member Profiling                         |
|  - Public Location-Based ASHA Worker Finder Portal (/api/workers/find)            |
|  - Real-time Field Register Dashboard & Bilingual Support (English / Kannada)     |
+-----------------------------------------------------------------------------------+
```

---

## 📋 Phase 2 to Phase 3 Interface Contract

### Endpoint: `POST /api/visits/confirm`

The Phase 3 backend accepts and validates the worker-confirmed structured visit record produced by Phase 2:

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

### Validation & Rejection Invariants:
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

## 🗂️ Conflict File Reconciliation Strategy

All 11 conflict files were reconciled to ensure unified operation across Phase 1, Phase 2, and Phase 3:

| # | Conflict File | Reconciled Integration Strategy |
|---|---------------|----------------------------------|
| 1 | `.gitignore` | Combined ignore rules for Python (`__pycache__`, `.venv`, `*.db`), Node/Vite (`node_modules`, `dist`), Phase 1 audio streams (`*.wav`, `*.mp3`, `audio/`), Phase 2 AI checkpoints (`models/`, `.cache/`), and environment secrets (`.env`). |
| 2 | `README.md` | Comprehensive architectural documentation, data contracts, run instructions, and test commands. |
| 3 | `backend/main.py` | Single unified FastAPI instance. Mounts all Phase 3 routers alongside Phase 1 `voice_router` (`/ws/audio`, `/api/voice/transcribe`), loads environment variables safely, initializes SQLite WAL schema, and serves the frontend. |
| 4 | `backend/requirements.txt` | Merged backend requirements: `fastapi`, `uvicorn[standard]`, `pydantic`, `websockets`, `python-multipart`, `python-dotenv`, `httpx`, `pytest`. |
| 5 | `backend/routes/__init__.py` | Cleanly exports all routers without circular imports: `visits_router`, `beneficiaries_router`, `followups_router`, `reports_router`, `auth_router`, `areas_router`, `households_router`, `analytics_router`, `workers_router`, and `voice_router`. |
| 6 | `frontend/index.html` | Clean Vite HTML entry point importing `/src/main.jsx`, configured with Google Fonts (Plus Jakarta Sans, Noto Sans Kannada, Noto Sans Devanagari) and mobile-responsive viewport. |
| 7 | `frontend/package.json` | Dependencies for React 18, React DOM 18, Lucide React icons, and Vite build tooling. |
| 8 | `frontend/src/App.jsx` | Unified single frontend entry component integrating: (1) Phase 1 Voice Recorder with live waveform and language selection, (2) Phase 2 AI Extraction Review Card with explicit worker confirmation, and (3) Phase 3 Dashboard, Confirmed Visits Register, Follow-up Tracker, Household Directory with Edit/Delete, and Worker Finder. |
| 9 | `frontend/src/index.css` | Comprehensive CSS styles for responsive field layouts, pulse recording animations, waveform bars, status badges, and bilingual typography. |
| 10 | `frontend/src/main.jsx` | React 18 root mounting `App.jsx` into `#root`. |
| 11 | `frontend/vite.config.js` | Configured Vite proxy forwarding `/api` to `http://localhost:8000` and `/ws` to `ws://localhost:8000`. |

---

## 👥 Demo User Credentials (Role-Based Access Control)

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
- **Unified Field Register & Dashboard:** [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Live WebSocket Audio Endpoint:** `ws://localhost:8000/ws/audio`
- **System Health & Phase Status:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 3. (Optional) Run Vite Frontend in Development Mode
```powershell
cd "c:\Users\manju\Asha Sahayak\Asha-Sahayak\frontend"
& "C:\Program Files\nodejs\npm.cmd" run dev
```

---

## 🧪 Verification & Automated Test Suites

Run the automated test suites covering all integration contracts:

```powershell
cd "c:\Users\manju\Asha Sahayak\Asha-Sahayak"

# 1. Location-Based ASHA Worker Finder & Login Portal Verification (10 Scenarios)
& "C:\Users\manju\AppData\Local\Programs\Python\Python312\python.exe" tests/test_finder_portal.py

# 2. Household & Family Survey Edit and Delete Functionality (10 Scenarios)
& "C:\Users\manju\AppData\Local\Programs\Python\Python312\python.exe" -m unittest tests/test_edit_delete.py

# 3. Direct Route Handlers Execution Suite
& "C:\Users\manju\AppData\Local\Programs\Python\Python312\python.exe" -m unittest tests/test_route_functions.py
```
*(All 20+ test scenarios execute in < 1 second with 100% pass rate)*
