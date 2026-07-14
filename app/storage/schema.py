"""Versioned SQLite schema for local product data."""

SCHEMA_VERSION = 2

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classes (
    id TEXT PRIMARY KEY,
    class_name TEXT NOT NULL,
    grade_name TEXT NOT NULL DEFAULT '',
    school_year TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    class_id TEXT NOT NULL REFERENCES classes(id),
    student_no TEXT NOT NULL,
    name TEXT NOT NULL,
    aliases TEXT NOT NULL DEFAULT '[]',
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(class_id, student_no)
);

CREATE TABLE IF NOT EXISTS exam_sessions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    class_id TEXT NOT NULL REFERENCES classes(id),
    exam_name TEXT NOT NULL,
    answer_key_asset_id TEXT,
    paper_asset_id TEXT,
    template_id TEXT,
    teacher_confirmed INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exam_assets (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id),
    class_id TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS capture_jobs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id),
    class_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_path TEXT NOT NULL,
    stored_image_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    source_size INTEGER NOT NULL DEFAULT 0,
    source_mtime REAL NOT NULL DEFAULT 0,
    state TEXT NOT NULL,
    error_code TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(session_id, sha256)
);

CREATE TABLE IF NOT EXISTS mobile_capture_receipts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id),
    client_capture_id TEXT NOT NULL,
    capture_job_id TEXT NOT NULL REFERENCES capture_jobs(id),
    sha256 TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(session_id, client_capture_id)
);

CREATE TABLE IF NOT EXISTS recognition_drafts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id),
    class_id TEXT NOT NULL,
    capture_job_id TEXT NOT NULL REFERENCES capture_jobs(id),
    evidence_json TEXT NOT NULL,
    provisional_json TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_issues (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id),
    class_id TEXT NOT NULL,
    capture_job_id TEXT,
    issue_type TEXT NOT NULL,
    question_number INTEGER,
    teacher_message TEXT NOT NULL,
    evidence_path TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}',
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_resolutions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id),
    class_id TEXT NOT NULL,
    issue_id TEXT NOT NULL REFERENCES review_issues(id),
    teacher_action TEXT NOT NULL,
    manual_score REAL,
    reason TEXT NOT NULL,
    original_evidence_path TEXT NOT NULL,
    actor TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS final_submissions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id),
    class_id TEXT NOT NULL,
    student_id TEXT NOT NULL REFERENCES students(id),
    answers_json TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(session_id, student_id)
);

CREATE TABLE IF NOT EXISTS final_scores (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id),
    class_id TEXT NOT NULL,
    student_id TEXT NOT NULL REFERENCES students(id),
    student_no TEXT NOT NULL,
    student_name TEXT NOT NULL,
    score REAL NOT NULL,
    max_score REAL NOT NULL,
    percent REAL NOT NULL,
    unresolved_count INTEGER NOT NULL,
    manual_review_count INTEGER NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(session_id, student_id)
);

CREATE TABLE IF NOT EXISTS artifact_index (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id),
    class_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    class_id TEXT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_students_class ON students(class_id);
CREATE INDEX IF NOT EXISTS ix_sessions_class ON exam_sessions(class_id);
CREATE INDEX IF NOT EXISTS ix_jobs_session ON capture_jobs(session_id);
CREATE INDEX IF NOT EXISTS ix_mobile_receipts_session ON mobile_capture_receipts(session_id);
CREATE INDEX IF NOT EXISTS ix_issues_session_state ON review_issues(session_id, state);
"""
