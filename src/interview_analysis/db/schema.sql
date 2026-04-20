CREATE TABLE IF NOT EXISTS assessment_jobs (
    job_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    session_id TEXT NOT NULL,
    status TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT,
    report_json JSONB
);

CREATE INDEX IF NOT EXISTS idx_assessment_jobs_session_id
    ON assessment_jobs (session_id);

CREATE INDEX IF NOT EXISTS idx_assessment_jobs_status
    ON assessment_jobs (status);