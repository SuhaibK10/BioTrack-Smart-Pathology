-- ============================================================
--  BioTrack AI — PostgreSQL Schema
--  Run this in your Supabase SQL Editor
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Clinics (multi-tenant root) ──────────────────────────────
CREATE TABLE IF NOT EXISTS clinics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    subscription    TEXT NOT NULL DEFAULT 'free', -- free | pro | enterprise
    contact_email   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Patients ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id       UUID REFERENCES clinics(id) ON DELETE CASCADE,
    full_name       TEXT NOT NULL,
    dob             DATE,
    sex             TEXT CHECK (sex IN ('Male','Female','Other')),
    phone           TEXT,
    email           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patients_clinic ON patients(clinic_id);

-- ── Lab Reports ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lab_reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id      UUID REFERENCES patients(id) ON DELETE CASCADE,
    clinic_id       UUID REFERENCES clinics(id) ON DELETE CASCADE,
    lab_name        TEXT,
    patient_id_lab  TEXT,          -- Lab's own patient/visit ID
    report_date     DATE,
    file_url        TEXT,          -- Supabase Storage URL
    ocr_status      TEXT NOT NULL DEFAULT 'pending', -- pending|processing|done|failed
    raw_ocr_text    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_patient ON lab_reports(patient_id);
CREATE INDEX IF NOT EXISTS idx_reports_clinic  ON lab_reports(clinic_id);

-- ── Biomarker Records ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS biomarker_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id       UUID REFERENCES lab_reports(id) ON DELETE CASCADE,
    patient_id      UUID REFERENCES patients(id) ON DELETE CASCADE,
    test_name       TEXT NOT NULL,
    test_group      TEXT,
    value           NUMERIC,
    unit            TEXT,
    ref_low         NUMERIC,
    ref_high        NUMERIC,
    ref_text        TEXT,
    status          TEXT CHECK (status IN ('HIGH','LOW','NORMAL')),
    extracted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_biomarkers_patient ON biomarker_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_biomarkers_report  ON biomarker_records(report_id);
CREATE INDEX IF NOT EXISTS idx_biomarkers_name    ON biomarker_records(test_name);

-- ── Risk Assessments ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS risk_assessments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id       UUID REFERENCES lab_reports(id) ON DELETE CASCADE,
    patient_id      UUID REFERENCES patients(id) ON DELETE CASCADE,
    disease_cat     TEXT NOT NULL,
    risk_score      NUMERIC(5,4),   -- 0.0000 to 1.0000
    risk_label      TEXT,
    shap_json       JSONB,
    assessed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_patient ON risk_assessments(patient_id);

-- ── Alerts ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id      UUID REFERENCES patients(id) ON DELETE CASCADE,
    clinic_id       UUID REFERENCES clinics(id) ON DELETE CASCADE,
    report_id       UUID REFERENCES lab_reports(id) ON DELETE CASCADE,
    biomarker_name  TEXT NOT NULL,
    trigger_value   NUMERIC,
    unit            TEXT,
    severity        TEXT CHECK (severity IN ('critical','high','moderate')),
    title           TEXT,
    detail          TEXT,
    system_tag      TEXT,
    resolved        BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_patient ON alerts(patient_id);
CREATE INDEX IF NOT EXISTS idx_alerts_clinic  ON alerts(clinic_id);

-- ── Audit Log ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID,
    action      TEXT NOT NULL,
    table_name  TEXT,
    record_id   UUID,
    payload     JSONB,
    ip_address  INET,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Row-Level Security ────────────────────────────────────────
ALTER TABLE clinics           ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients          ENABLE ROW LEVEL SECURITY;
ALTER TABLE lab_reports       ENABLE ROW LEVEL SECURITY;
ALTER TABLE biomarker_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_assessments  ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts            ENABLE ROW LEVEL SECURITY;

-- Allow all for service role (backend)
-- Clinic-scoped policies can be added per your auth model.

-- ── Seed: Default clinic ──────────────────────────────────────
INSERT INTO clinics (id, name, subscription, contact_email)
VALUES (
    'a1b2c3d4-0000-0000-0000-000000000001',
    'JNMC Department of Pathology, AMU',
    'pro',
    'pathology@jnmc.amu.ac.in'
) ON CONFLICT (id) DO NOTHING;

-- ── Seed: Demo patient (Jahangir Khan) ────────────────────────
INSERT INTO patients (id, clinic_id, full_name, dob, sex, phone)
VALUES (
    'b2c3d4e5-0000-0000-0000-000000000001',
    'a1b2c3d4-0000-0000-0000-000000000001',
    'Jahangir Khan',
    '1937-01-01',
    'Male',
    NULL
) ON CONFLICT (id) DO NOTHING;
