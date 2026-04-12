CREATE OR REPLACE VIEW analytics.module_failure_rates AS
SELECT
    ai_module_id,
    ai_module_name,
    COUNT(*) AS total_runs,
    COUNT(*) FILTER (WHERE run_status = 'failed') AS failed_runs,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE run_status = 'failed') / NULLIF(COUNT(*), 0),
        2
    ) AS failure_rate_pct
FROM analytics.fact_module_runs
GROUP BY ai_module_id, ai_module_name;
