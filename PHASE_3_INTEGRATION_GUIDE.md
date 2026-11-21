# ASHA SAHAYAK – PHASE 3: DATABASE, DASHBOARD AND FOLLOW-UP MANAGEMENT

## Overview & Architecture
Phase 3 is responsible for receiving worker-confirmed structured visit records from Phase 2, persisting them securely in an SQLite database, preventing duplicates, scheduling follow-ups without inventing dates, and presenting a clean, accessible, mobile-responsive dashboard for ASHA workers.

```
+-----------------------------------------------------------+
|               Phase 2: Confirmation Module                |
|  Worker confirms voice-extracted structured visit record  |
+-----------------------------+-----------------------------+
                              |
                     POST /api/visits/confirm
                              |
                              v
+-----------------------------------------------------------+
|             Phase 3: Shared FastAPI Backend               |
|  - JSON Schema & Status Validation                        |
|  - Duplicate Submission Prevention (SHA-256 Checksum)     |
|  - Safe Follow-up Scheduling (No Date Fabrication)        |
|  - PHC Referral Flagging & Danger Signs Retention         |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|              SQLite Database (Thread-Safe WAL)            |
|  - beneficiaries  (Synthetic Master Profiles)             |
|  - visits         (Confirmed Visit Records & Auditing)    |
|  - follow_ups     (Scheduled, Overdue & Completed Visits) |
+-----------------------------+-----------------------------+
                              |
                     GET /api/reports, /api/beneficiaries...
                              |
                              v
+-----------------------------------------------------------+
|              ASHA Worker React Field Dashboard            |
|  - High-Contrast Legible UI for Field Smartphones         |
|  - Urgent PHC Referral Alerts & Predefined Danger Signs   |
|  - Search by Beneficiary ID (e.g. BNF-2041)               |
|  - Follow-up Management & Worker Field Notes              |
|  - Built-in Phase 2 Ingestion Testing Simulator           |
+-----------------------------------------------------------+
```

---

## 1. Input Contract from Phase 2

### Agreed JSON Schema
The endpoint `POST /api/visits/confirm` accepts and validates this exact JSON payload:

```json
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
```

### Validation & Rejection Rules
1. **Confirmation Status Enforcement:**
   - Only records with `"confirmation_status": "confirmed"` are persisted.
   - Any record with `"pending"`, `"unconfirmed"`, or missing status is rejected with **HTTP 400 Bad Request**.
2. **Duplicate Submission Prevention:**
   - Deterministic SHA-256 fingerprint generated from `beneficiary_id + visit_type + visit_date + weight + vaccinations_due`.
   - Repeated submissions of the exact same visit return **HTTP 409 Conflict**.
3. **Follow-up Date Integrity:**
   - If `next_visit_date` is `null` (like in BNF-2041), the system **does not invent a follow-up date**.
   - If `next_visit_date` is provided (e.g., `"2026-12-05"`), an upcoming follow-up record is automatically created.
4. **Referral Alerts without Algorithmic Diagnosis:**
   - If `referral_required` is `true` or `danger_signs` are present, the record is flagged for Primary Health Centre (PHC) follow-up. The system does not independently diagnose beneficiaries.

---

## 2. Database Schema (SQLite)

The database uses SQLite with Foreign Key constraints (`PRAGMA foreign_keys = ON;`) and Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) for high concurrency.

### Tables
1. **`beneficiaries`**
   - `beneficiary_id` (TEXT PRIMARY KEY, e.g. "BNF-2041")
   - `full_name` (TEXT NOT NULL, synthetic)
   - `age_years` (INTEGER)
   - `gender` (TEXT)
   - `category` (TEXT, e.g. "Lactating Mother / Newborn", "Pregnant Woman")
   - `village_ward` (TEXT, e.g. "Rampur - Ward 4")
   - `contact_number` (TEXT, synthetic masked)
   - `notes` (TEXT)
   - `created_at` (TEXT ISO timestamp)
   - `updated_at` (TEXT ISO timestamp)

2. **`visits`**
   - `visit_id` (TEXT PRIMARY KEY, e.g. "VIS-3AB519DE")
   - `beneficiary_id` (TEXT REFERENCES beneficiaries)
   - `visit_type` (TEXT NOT NULL)
   - `weight` (TEXT, e.g. "3.2 kg")
   - `vaccinations_due` (TEXT JSON array)
   - `next_visit_date` (TEXT ISO date YYYY-MM-DD or NULL)
   - `danger_signs` (TEXT JSON array)
   - `referral_required` (INTEGER 0 or 1)
   - `referral_facility` (TEXT)
   - `referral_status` (TEXT, e.g. "Pending PHC Referral", "Not Required")
   - `confirmation_status` (TEXT, must be "confirmed")
   - `submission_hash` (TEXT UNIQUE)
   - `visit_date` (TEXT ISO date)
   - `created_at` (TEXT ISO timestamp)

3. **`follow_ups`**
   - `followup_id` (TEXT PRIMARY KEY, e.g. "FOL-8001")
   - `visit_id` (TEXT REFERENCES visits)
   - `beneficiary_id` (TEXT REFERENCES beneficiaries)
   - `scheduled_date` (TEXT ISO date YYYY-MM-DD)
   - `status` (TEXT: 'upcoming', 'overdue', 'completed', 'cancelled')
   - `reason` (TEXT)
   - `worker_notes` (TEXT)
   - `updated_by` (TEXT)
   - `completed_at` (TEXT ISO timestamp)
   - `created_at` (TEXT ISO timestamp)
   - `updated_at` (TEXT ISO timestamp)

---

## 3. API Endpoints Reference

All endpoints are hosted on the shared FastAPI application:

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `POST` | `/api/visits/confirm` | Ingests worker-confirmed Phase 2 record | `201`, `400`, `409`, `422` |
| `GET` | `/api/visits` | Lists completed visits (filterable by `beneficiary_id`) | `200` |
| `GET` | `/api/beneficiaries` | Lists beneficiaries (supports `?search=` by ID/name) | `200` |
| `GET` | `/api/beneficiaries/{id}` | Full profile, visit history, vaccinations & follow-ups | `200`, `404` |
| `GET` | `/api/followups` | Lists follow-ups (filterable by `?status=upcoming/overdue`) | `200` |
| `PATCH` | `/api/followups/{id}/status` | Updates follow-up status & records worker field notes | `200`, `400`, `404` |
| `GET` | `/api/reports` | Aggregated dashboard metrics, vaccination summary | `200` |
| `POST` | `/api/reports/reset-demo` | Resets to clean synthetic demo state | `200` |
| `GET` | `/api/health` | Healthcheck and active database status | `200` |

---

## 4. Synthetic Demo Records

For hackathon presentation, the database pre-seeds realistic synthetic records:

- **`BNF-2041`** – Pooja Sharma (Age 22, Rampur Ward 4). Lactating Mother with newborn baby Aarav. Target beneficiary for Phase 2 newborn home visit test.
- **`BNF-1082`** – Kavita Devi (Age 26, Kalyanpur Ward 2). 3rd Trimester Pregnant Woman (32 weeks). Due for TT-2 & IFA tablets.
- **`BNF-3094`** – Meena Kumari (Age 19, Shantipura Ward 1). First-time mother with 3-day newborn. Overdue neonatal jaundice follow-up.
- **`BNF-4105`** – Sunita Patel (Age 28, Rampur Ward 5). High-risk pregnancy flagged for severe anemia (Hb 7.8 g/dL). Prominently marked for PHC referral.
- **`BNF-5219`** – Anita Verma (Age 24, Kalyanpur Ward 3). Mother of 9-month infant due for MR-1 (Measles-Rubella) & Vitamin A.

---

## 5. Setup & Running Instructions

### Prerequisites
- Python 3.10+
- Modern Web Browser (Chrome, Edge, Firefox, Brave)

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Run the Shared FastAPI Application
From the repository root:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- Open browser at `http://localhost:8000` to view the interactive ASHA Dashboard.
- Open Swagger API documentation at `http://localhost:8000/docs`.

### 3. Run Automated Tests
```bash
pytest tests/test_phase3.py -v
```

---

## 6. Built-in Phase 2 Ingestion Simulator
The dashboard includes an interactive **"Phase 2 Ingestion Simulator"** tab.
1. Click **"Exact Phase 2 Payload (BNF-2041)"** to load the Phase 2 contract JSON.
2. Click **"Submit to /api/visits/confirm"** to test live transmission.
3. Observe the `HTTP 201 Created` response.
4. Click submit again to observe the duplicate prevention mechanism returning `HTTP 409 Conflict`.
5. Click **"Unconfirmed / Pending"** to observe `HTTP 400 Bad Request` rejection.
