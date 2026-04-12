CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.requests (
    request_id TEXT PRIMARY KEY,
    hospital_id TEXT NOT NULL,
    disease_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    requested_at TIMESTAMP NOT NULL,
    expected_image_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.image_upload_events (
    upload_event_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    image_id TEXT NOT NULL,
    uploaded_at TIMESTAMP NOT NULL,
    storage_bucket TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.processing_jobs (
    job_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    ai_module_id TEXT NOT NULL,
    queued_at TIMESTAMP NOT NULL,
    final_status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.module_runs (
    run_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    ai_module_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    run_status TEXT NOT NULL,
    error_category TEXT
);

CREATE TABLE IF NOT EXISTS raw.job_status_events (
    job_status_event_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_time TIMESTAMP NOT NULL,
    event_detail TEXT
);
