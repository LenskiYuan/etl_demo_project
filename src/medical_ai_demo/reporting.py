from __future__ import annotations

from collections import defaultdict
from statistics import mean


def _safe_mean(values: list[float]) -> float:
    return round(mean(values), 2) if values else 0.0


def build_summary_report(
    fact_job_lifecycle: list[dict[str, object]],
    fact_module_runs: list[dict[str, object]],
) -> str:
    total_jobs = len(fact_job_lifecycle)
    failed_jobs = sum(1 for row in fact_job_lifecycle if row["job_final_status"] == "failed")
    queue_delays = [float(row["queue_delay_minutes"]) for row in fact_job_lifecycle]
    request_to_upload = [float(row["request_to_upload_complete_minutes"]) for row in fact_job_lifecycle]
    upload_to_start = [float(row["upload_complete_to_processing_start_minutes"]) for row in fact_job_lifecycle]
    end_to_end = [float(row["end_to_end_minutes"]) for row in fact_job_lifecycle]
    processing_durations = [float(row["run_duration_minutes"]) for row in fact_module_runs]

    by_module: dict[str, dict[str, float]] = defaultdict(lambda: {"total": 0, "failed": 0})
    for row in fact_module_runs:
        key = str(row["ai_module_name"])
        by_module[key]["total"] += 1
        if row["run_status"] == "failed":
            by_module[key]["failed"] += 1

    module_lines = []
    for module_name, values in sorted(by_module.items()):
        failure_rate = 0.0 if values["total"] == 0 else round((values["failed"] / values["total"]) * 100, 2)
        module_lines.append(f"- {module_name}: {int(values['failed'])} failed runs out of {int(values['total'])} ({failure_rate}%)")

    breach_count = sum(1 for row in fact_job_lifecycle if row["queue_sla_breached"] == "true" or row["end_to_end_sla_breached"] == "true")
    failure_rate = 0.0 if total_jobs == 0 else round((failed_jobs / total_jobs) * 100, 2)

    return "\n".join(
        [
            "# Observability Summary",
            "",
            f"- Total jobs: {total_jobs}",
            f"- Failed jobs: {failed_jobs} ({failure_rate}%)",
            f"- Average request-to-upload-complete latency: {_safe_mean(request_to_upload)} minutes",
            f"- Average upload-complete-to-processing-start latency: {_safe_mean(upload_to_start)} minutes",
            f"- Average queue delay: {_safe_mean(queue_delays)} minutes",
            f"- Average end-to-end time: {_safe_mean(end_to_end)} minutes",
            f"- Average module run duration: {_safe_mean(processing_durations)} minutes",
            f"- Jobs with SLA breaches: {breach_count}",
            "",
            "## Module Failure Rates",
            "",
            *module_lines,
            "",
        ]
    )

