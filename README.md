# Asha-Sahayak
**Asha Sahayak (आशा सहायक / ಆಶಾ ಸಹಾಯಕ)** – An AI-powered voice-based field register, household survey, and community healthcare management system designed to empower ASHA workers and Primary Health Centres (PHCs).

---

## 🌟 Key Features

### 1. Multi-Role Login & Security
- **Roles:**
  - **Administrator:** Global oversight of all areas, taluks, workers, and households.
  - **ASHA Worker:** Strictly scoped to her designated village and postal PIN code.
  - **Health Supervisor:** Oversight of assigned taluks, subcenters, and field surveys.
- **Login Credentials (Demo):**
  - Administrator: `admin` / `admin123`
  - ASHA Worker (Rampur): `asha_rampur` / `asha123` (PIN: `571428`)
  - ASHA Worker (Kalyanpur): `asha_kalyanpur` / `asha123` (PIN: `571434`)
  - Health Supervisor: `supervisor_maddur` / `sup123`
- Show/Hide password toggle and password assistance.

### 2. Location-Based Access Scoping
- Each ASHA worker is assigned to a specific geographical unit (State, District, Taluk, Village, Area, PIN Code).
- Workers can only view, register, and update households in their designated area.
- Cross-area unauthorized access attempts are blocked with `HTTP 403 Forbidden`.

### 3. Family & Household Survey Module
- **Household Registration:** Unique sequential IDs (e.g. `HH-571428-001`), family head, address, housing type (Pucca/Semi-Pucca/Kutcha), drinking water source, toilet availability (IHHL), sanitation facility.
- **Duplicate Prevention:** Identifies duplicate household registrations at the same address.
- **Individual Health Profiling:** Add multiple family members with targeted health indicators:
  - Pregnant women (with trimester tracking)
  - Lactating mothers
  - Children under 5 & immunization backlog
  - Elderly residents (60+)
  - Persons with disabilities & chronic conditions
- **Survey Lifecycle:** Save as Draft or Submit Completed Survey.

### 4. Interactive Dashboard & Analytics
- Demographic breakdown (Male, Female, Children under 5, Elderly).
- Maternal & child health trackers.
- Water and sanitation infrastructure breakdown.
- Dynamic filters by PIN code, Village, and Worker.

### 5. Household Directory
- Searchable directory by household code, head of family, address, or PIN code.
- Detailed modal displaying complete family demographic profile, health flags, and audit history.

### 6. Bilingual User Interface
- One-click toggle between **English** and **ಕನ್ನಡ (Kannada)**.
- High-contrast, mobile-friendly design for field smartphones and tablets.

### 7. Preserved Phase 2 & 3 Visit Registers
- Structured visit records from Phase 2 (`POST /api/visits/confirm`) with duplicate prevention.
- Follow-up management without date fabrication.
- Emergency referral alerts and danger sign retention.
- Interactive **Phase 2 Ingestion Simulator** built into the dashboard.

---

## 🚀 Quick Start Instructions

### 1. Start Backend & Dashboard Server
```powershell
cd "c:\Users\manju\Asha Sahayak\Asha-Sahayak"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Open in Browser
- **Dashboard:** [http://localhost:8000/](http://localhost:8000/)
- **Swagger API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Run Automated Tests
```powershell
python -m pytest tests/ -v
```
*(All 20 unit and integration tests passing)*
