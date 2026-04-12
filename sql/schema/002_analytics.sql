CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.dim_hospital (
    hospital_id TEXT PRIMARY KEY,
    hospital_name TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_disease (
    disease_type TEXT PRIMARY KEY,
    ai_module_id TEXT NOT NULL,
    ai_module_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_ai_module (
    ai_module_id TEXT PRIMARY KEY,
    ai_module_name TEXT NOT NULL,
    supported_disease TEXT NOT NULL,
    baseline_duration_minutes INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.fact_job_lifecycle (
    job_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    hospital_id TEXT NOT NULL,
    disease_type TEXT NOT NULL,
    ai_module_id TEXT NOT NULL,
    ai_module_name TEXT NOT NULL,
    requested_at TIMESTAMP NOT NULL,
    upload_completed_at TIMESTAMP NOT NULL,
    queued_at TIMESTAMP NOT NULL,
    processing_started_at TIMESTAMP NOT NULL,
    processing_completed_at TIMESTAMP NOT NULL,
    attempt_count INTEGER NOT NULL,
    job_final_status TEXT NOT NULL,
    request_to_upload_complete_minutes NUMERIC(10,2) NOT NULL,
    upload_complete_to_processing_start_minutes NUMERIC(10,2) NOT NULL,
    queue_delay_minutes NUMERIC(10,2) NOT NULL,
    end_to_end_minutes NUMERIC(10,2) NOT NULL,
    queue_sla_breached BOOLEAN NOT NULL,
    end_to_end_sla_breached BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.fact_module_runs (
    run_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    hospital_id TEXT NOT NULL,
    disease_type TEXT NOT NULL,
    ai_module_id TEXT NOT NULL,
    ai_module_name TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    run_status TEXT NOT NULL,
    error_category TEXT,
    run_duration_minutes NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.daily_metrics (
    metric_date DATE NOT NULL,
    ai_module_id TEXT NOT NULL,
    ai_module_name TEXT NOT NULL,
    job_count INTEGER NOT NULL,
    failed_job_count INTEGER NOT NULL,
    failure_rate_pct NUMERIC(10,2) NOT NULL,
    avg_queue_delay_minutes NUMERIC(10,2) NOT NULL,
    avg_end_to_end_minutes NUMERIC(10,2) NOT NULL
);
