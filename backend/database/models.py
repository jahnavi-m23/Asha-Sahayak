"""
Database Table Schemas for ASHA Sahayak
Stores Users (RBAC), Areas, Households, Family Members, Surveys,
Beneficiaries, Completed Visits, and Follow-ups with strict audit timestamps.
"""

CREATE_TABLES_SQL = """
-- Users and Authentication table (Role-Based Access Control)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,              -- 'admin', 'asha_worker', 'health_supervisor'
    full_name TEXT NOT NULL,
    mobile TEXT,
    assigned_area_id TEXT,          -- Scoped area ID for ASHA workers
    badge_id TEXT,                  -- Official public identifier e.g. 'ASHA-KA-MDY-001'
    phc_name TEXT DEFAULT 'Primary Health Centre',
    work_contact TEXT,              -- Approved work contact number
    is_verified INTEGER DEFAULT 1,  -- 1 = Verified & Approved by Health Officer, 0 = Pending
    is_active INTEGER DEFAULT 1,    -- 1 = Active, 0 = Inactive / Deactivated
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- Geographical Areas and PIN Code Assignment table
CREATE TABLE IF NOT EXISTS areas (
    id TEXT PRIMARY KEY,
    state TEXT NOT NULL DEFAULT 'Karnataka',
    district TEXT NOT NULL,          -- e.g. 'Mandya', 'Ramanagara', 'Mysuru'
    taluk TEXT NOT NULL,             -- e.g. 'Maddur', 'Channapatna', 'Pandavapura'
    village TEXT NOT NULL,           -- e.g. 'Rampur', 'Kalyanpur', 'Shantipura'
    area_name TEXT NOT NULL,         -- e.g. 'Ward 4 - Anganwadi Sector 2'
    pincode TEXT NOT NULL,           -- e.g. '571428'
    phc_name TEXT DEFAULT 'Kestur Primary Health Centre',
    assigned_worker_id TEXT,         -- Foreign key to users table
    latitude REAL,                   -- Geographic latitude
    longitude REAL,                  -- Geographic longitude
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- Many-to-many Worker to Area allocations (supports multiple localities per worker / multiple workers per village)
CREATE TABLE IF NOT EXISTS worker_area_assignments (
    id TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL,
    area_id TEXT NOT NULL,
    is_primary INTEGER DEFAULT 1,
    assigned_at TEXT NOT NULL,
    FOREIGN KEY (worker_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (area_id) REFERENCES areas (id) ON DELETE CASCADE
);

-- Audit logs for Administrator and Supervisor actions
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,            -- 'WORKER_REGISTERED', 'AREA_REASSIGNED', 'STATUS_CHANGED', 'PASSWORD_RESET'
    performed_by TEXT NOT NULL,      -- User ID or username
    target_entity TEXT,              -- 'USER', 'AREA', 'HOUSEHOLD'
    target_id TEXT,                  -- Target entity ID
    details TEXT,                    -- Human-readable details
    created_at TEXT NOT NULL
);

-- Households table
CREATE TABLE IF NOT EXISTS households (
    id TEXT PRIMARY KEY,
    household_code TEXT UNIQUE NOT NULL, -- e.g. 'HH-571428-001'
    area_id TEXT NOT NULL,
    head_of_family TEXT NOT NULL,
    address TEXT NOT NULL,
    pincode TEXT NOT NULL,
    village TEXT NOT NULL,
    contact_number TEXT,
    house_type TEXT NOT NULL DEFAULT 'Pucca', -- 'Pucca', 'Semi-Pucca', 'Kutcha'
    water_source TEXT NOT NULL DEFAULT 'Piped Water / Tap', -- 'Piped Water / Tap', 'Borewell / Handpump', 'Well', 'Filter Plant / RO'
    toilet_available TEXT NOT NULL DEFAULT 'Individual Household Latrine (IHHL)', -- 'Individual Household Latrine (IHHL)', 'Community Toilet', 'None / Open'
    sanitation_facility TEXT NOT NULL DEFAULT 'Closed Drainage', -- 'Closed Drainage', 'Soak Pit', 'Open Drain'
    survey_status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'draft', 'completed', 'verified'
    created_by_worker_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (area_id) REFERENCES areas (id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_worker_id) REFERENCES users (id) ON DELETE RESTRICT
);

-- Individual Family Members under Households
CREATE TABLE IF NOT EXISTS family_members (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL,
    full_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,            -- 'Male', 'Female', 'Other'
    dob TEXT,
    relationship TEXT NOT NULL,      -- 'Self / Head', 'Spouse', 'Son', 'Daughter', 'Father', 'Mother', 'Daughter-in-law', 'Grandchild', 'Other'
    mobile TEXT,
    occupation TEXT,
    education TEXT,                  -- 'Illiterate', 'Primary', 'Secondary', 'Higher Secondary', 'Graduate & Above'
    marital_status TEXT,             -- 'Unmarried', 'Married', 'Widowed', 'Separated / Divorced'
    
    -- Configurable Health Information
    is_pregnant INTEGER DEFAULT 0,
    pregnancy_trimester TEXT,        -- '1st Trimester', '2nd Trimester', '3rd Trimester'
    is_lactating INTEGER DEFAULT 0,
    lactating_child_age_months INTEGER,
    is_child_under_5 INTEGER DEFAULT 0,
    requires_immunization INTEGER DEFAULT 0,
    immunization_due TEXT,           -- Comma-separated or JSON list
    is_elderly INTEGER DEFAULT 0,    -- 60+ years
    has_disability INTEGER DEFAULT 0,
    disability_type TEXT,
    chronic_conditions TEXT,         -- e.g. 'Hypertension, Diabetes'
    current_medications TEXT,
    recent_checkup_date TEXT,
    nutritional_status TEXT DEFAULT 'Normal', -- 'Normal', 'MAM', 'SAM'
    special_needs TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (household_id) REFERENCES households (id) ON DELETE CASCADE
);

-- Surveys Tracking and Auditing table
CREATE TABLE IF NOT EXISTS surveys (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL,
    worker_id TEXT NOT NULL,
    survey_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed', -- 'draft', 'completed', 'verified'
    remarks TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (household_id) REFERENCES households (id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES users (id) ON DELETE RESTRICT
);

-- Beneficiary master table (Preserved from Phase 3)
CREATE TABLE IF NOT EXISTS beneficiaries (
    beneficiary_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    age_years INTEGER,
    gender TEXT DEFAULT 'Female',
    category TEXT NOT NULL,
    village_ward TEXT NOT NULL,
    contact_number TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Visits table: stores confirmed visit records from Phase 2 (Preserved from Phase 3)
CREATE TABLE IF NOT EXISTS visits (
    visit_id TEXT PRIMARY KEY,
    beneficiary_id TEXT NOT NULL,
    beneficiary_name TEXT,
    age INTEGER,
    visit_type TEXT NOT NULL,
    weight TEXT,
    blood_pressure TEXT,
    gestational_age TEXT,
    vaccinations_due TEXT,
    symptoms_reported TEXT,
    negated_symptoms TEXT,
    next_visit_date TEXT,
    danger_signs TEXT,
    referral_required INTEGER NOT NULL DEFAULT 0,
    referral_facility TEXT,
    referral_status TEXT DEFAULT 'Not Required',
    confirmation_status TEXT NOT NULL,
    raw_transcript TEXT,
    worker_id TEXT,
    submission_hash TEXT UNIQUE,
    visit_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries (beneficiary_id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Voice records table: persists audio transcriptions and extracted structured reports across Phase 1 & 2
CREATE TABLE IF NOT EXISTS voice_records (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    worker_id TEXT,
    form_type TEXT DEFAULT 'clinical_visit',
    transcript TEXT NOT NULL,
    language TEXT NOT NULL,
    structured_data TEXT,
    confidence_score REAL DEFAULT 1.0,
    status TEXT DEFAULT 'completed',
    submission_hash TEXT UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (worker_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Follow-up management table (Preserved from Phase 3)
CREATE TABLE IF NOT EXISTS follow_ups (
    followup_id TEXT PRIMARY KEY,
    visit_id TEXT,
    beneficiary_id TEXT NOT NULL,
    scheduled_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'upcoming',
    reason TEXT NOT NULL,
    worker_notes TEXT,
    updated_by TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (visit_id) REFERENCES visits (visit_id) ON DELETE SET NULL,
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries (beneficiary_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_areas_pincode ON areas(pincode);
CREATE INDEX IF NOT EXISTS idx_areas_village ON areas(village);
CREATE INDEX IF NOT EXISTS idx_areas_taluk ON areas(taluk);
CREATE INDEX IF NOT EXISTS idx_areas_district ON areas(district);
CREATE INDEX IF NOT EXISTS idx_areas_worker ON areas(assigned_worker_id);
CREATE INDEX IF NOT EXISTS idx_waa_worker ON worker_area_assignments(worker_id);
CREATE INDEX IF NOT EXISTS idx_waa_area ON worker_area_assignments(area_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_households_area ON households(area_id);
CREATE INDEX IF NOT EXISTS idx_households_pincode ON households(pincode);
CREATE INDEX IF NOT EXISTS idx_households_village ON households(village);
CREATE INDEX IF NOT EXISTS idx_households_worker ON households(created_by_worker_id);
CREATE INDEX IF NOT EXISTS idx_households_status ON households(survey_status);
CREATE INDEX IF NOT EXISTS idx_members_household ON family_members(household_id);
CREATE INDEX IF NOT EXISTS idx_surveys_household ON surveys(household_id);
CREATE INDEX IF NOT EXISTS idx_surveys_worker ON surveys(worker_id);
CREATE INDEX IF NOT EXISTS idx_visits_beneficiary ON visits(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(visit_date);
CREATE INDEX IF NOT EXISTS idx_visits_referral ON visits(referral_required);
CREATE INDEX IF NOT EXISTS idx_followups_beneficiary ON follow_ups(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_followups_scheduled ON follow_ups(scheduled_date);
"""

CREATE_MIGRATION_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_visits_worker ON visits(worker_id);
CREATE INDEX IF NOT EXISTS idx_voice_records_worker ON voice_records(worker_id);
CREATE INDEX IF NOT EXISTS idx_voice_records_created ON voice_records(created_at);
"""
