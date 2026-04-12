# Architecture Notes

## Goal

Model the operational lifecycle of a synthetic medical AI imaging workflow and expose it through an authenticated, multi-user platform with live database-backed monitoring.

## Pipeline Stages

1. **Generation**
   Raw operational records are created for:
   - imaging requests
   - image uploads
   - processing jobs
   - per-attempt module runs
   - job status events

2. **Transformation**
   The ETL layer builds:
   - `dim_hospital`
   - `dim_disease`
   - `dim_ai_module`
   - `fact_job_lifecycle`
   - `fact_module_runs`
   - `daily_metrics`

3. **Application Layer**
   - FastAPI validates Keycloak-issued bearer tokens
   - PostgreSQL serves both analytics queries and persistent app state
   - Celery workers execute ETL jobs asynchronously
   - React renders the dashboard and triggers runs through the API

4. **Reporting**
   Summary metrics are emitted as markdown for recruiter-friendly review and as SQL-backed API responses for the frontend.

## Modeling Choices

- A request can produce one logical processing job.
- A job can contain multiple module run attempts because retry behavior is important for observability.
- Queue delay and upload latency are modeled separately because they answer different operational questions.
- SLA flags are materialized in the lifecycle fact table to keep simple monitoring queries easy.
- Warehouse tables are refreshed as a latest snapshot, while application tables preserve job history and user-specific saved views.

## Public-Safe Constraints

- no private customer or hospital details
- no proprietary schema carryover
- no internal dashboard exports
- no real-world performance data

Everything here is synthetic and intentionally simplified.
