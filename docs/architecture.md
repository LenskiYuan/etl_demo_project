# Architecture Notes

## Goal

Model the operational lifecycle of a synthetic medical AI imaging workflow and turn raw events into monitoring-friendly analytical tables.

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

3. **Reporting**
   Summary metrics are emitted as markdown for recruiter-friendly review and as CSV for downstream visualization.

## Modeling Choices

- A request can produce one logical processing job.
- A job can contain multiple module run attempts because retry behavior is important for observability.
- Queue delay and upload latency are modeled separately because they answer different operational questions.
- SLA flags are materialized in the lifecycle fact table to keep simple monitoring queries easy.

## Public-Safe Constraints

- no private customer or hospital details
- no proprietary schema carryover
- no internal dashboard exports
- no real-world performance data

Everything here is synthetic and intentionally simplified.
