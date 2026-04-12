from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from .config import build_output_paths, ensure_output_dirs
from .generator import DISEASE_MODULES, HOSPITALS, generate_demo_data
from .postgres_loader import build_copy_manifest
from .reporting import build_summary_report


DATETIME_FIELDS = {
    "requested_at",
    "uploaded_at",
    "queued_at",
    "started_at",
    "completed_at",
    "event_time",
    "upload_completed_at",
    "processing_started_at",
    "processing_completed_at",
}


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _minutes_between(start: datetime, end: datetime) -> float:
    return round((end - start).total_seconds() / 60, 2)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def generate_raw(output_root: Path, request_count: int, seed: int) -> None:
    paths = build_output_paths(output_root)
    ensure_output_dirs(paths)
    demo_data = generate_demo_data(request_count=request_count, seed=seed)
    _write_csv(paths.raw_dir / "requests.csv", demo_data.requests)
    _write_csv(paths.raw_dir / "image_upload_events.csv", demo_data.image_upload_events)
    _write_csv(paths.raw_dir / "processing_jobs.csv", demo_data.processing_jobs)
    _write_csv(paths.raw_dir / "module_runs.csv", demo_data.module_runs)
    _write_csv(paths.raw_dir / "job_status_events.csv", demo_data.job_status_events)


def _bool_string(value: bool) -> str:
    return "true" if value else "false"


def build_analytics(output_root: Path) -> dict[str, list[dict[str, object]]]:
    paths = build_output_paths(output_root)
    requests = _read_csv(paths.raw_dir / "requests.csv")
    image_upload_events = _read_csv(paths.raw_dir / "image_upload_events.csv")
    processing_jobs = _read_csv(paths.raw_dir / "processing_jobs.csv")
    module_runs = _read_csv(paths.raw_dir / "module_runs.csv")

    request_by_id = {row["request_id"]: row for row in requests}
    uploads_by_request: dict[str, list[dict[str, str]]] = {}
    for row in image_upload_events:
        uploads_by_request.setdefault(row["request_id"], []).append(row)

    runs_by_job: dict[str, list[dict[str, str]]] = {}
    for row in module_runs:
        runs_by_job.setdefault(row["job_id"], []).append(row)

    dim_hospital = [dict(row) for row in HOSPITALS]
    dim_disease = [
        {"disease_type": disease_type, "ai_module_id": attrs["ai_module_id"], "ai_module_name": attrs["ai_module_name"]}
        for disease_type, attrs in DISEASE_MODULES.items()
    ]
    dim_ai_module = [
        {
            "ai_module_id": attrs["ai_module_id"],
            "ai_module_name": attrs["ai_module_name"],
            "supported_disease": disease_type,
            "baseline_duration_minutes": attrs["base_minutes"],
        }
        for disease_type, attrs in DISEASE_MODULES.items()
    ]

    fact_job_lifecycle: list[dict[str, object]] = []
    fact_module_runs: list[dict[str, object]] = []

    for job in processing_jobs:
        request = request_by_id[job["request_id"]]
        uploads = sorted(uploads_by_request[job["request_id"]], key=lambda row: row["uploaded_at"])
        runs = sorted(runs_by_job[job["job_id"]], key=lambda row: int(row["attempt_number"]))
        first_run = runs[0]
        last_run = runs[-1]

        requested_at = _parse_ts(request["requested_at"])
        upload_completed_at = _parse_ts(uploads[-1]["uploaded_at"])
        queued_at = _parse_ts(job["queued_at"])
        processing_started_at = _parse_ts(first_run["started_at"])
        processing_completed_at = _parse_ts(last_run["completed_at"])

        module_name = next(attrs["ai_module_name"] for attrs in DISEASE_MODULES.values() if attrs["ai_module_id"] == job["ai_module_id"])

        fact_job_lifecycle.append(
            {
                "job_id": job["job_id"],
                "request_id": job["request_id"],
                "hospital_id": request["hospital_id"],
                "disease_type": request["disease_type"],
                "ai_module_id": job["ai_module_id"],
                "ai_module_name": module_name,
                "requested_at": request["requested_at"],
                "upload_completed_at": upload_completed_at.isoformat(timespec="seconds"),
                "queued_at": job["queued_at"],
                "processing_started_at": first_run["started_at"],
                "processing_completed_at": last_run["completed_at"],
                "attempt_count": job["attempt_count"],
                "job_final_status": job["final_status"],
                "request_to_upload_complete_minutes": _minutes_between(requested_at, upload_completed_at),
                "upload_complete_to_processing_start_minutes": _minutes_between(upload_completed_at, processing_started_at),
                "queue_delay_minutes": _minutes_between(queued_at, processing_started_at),
                "end_to_end_minutes": _minutes_between(requested_at, processing_completed_at),
                "queue_sla_breached": _bool_string(_minutes_between(queued_at, processing_started_at) > 45),
                "end_to_end_sla_breached": _bool_string(_minutes_between(requested_at, processing_completed_at) > 240),
            }
        )

        for run in runs:
            started_at = _parse_ts(run["started_at"])
            completed_at = _parse_ts(run["completed_at"])
            fact_module_runs.append(
                {
                    "run_id": run["run_id"],
                    "job_id": run["job_id"],
                    "request_id": run["request_id"],
                    "hospital_id": request["hospital_id"],
                    "disease_type": request["disease_type"],
                    "ai_module_id": run["ai_module_id"],
                    "ai_module_name": module_name,
                    "attempt_number": run["attempt_number"],
                    "started_at": run["started_at"],
                    "completed_at": run["completed_at"],
                    "run_status": run["run_status"],
                    "error_category": run["error_category"],
                    "run_duration_minutes": _minutes_between(started_at, completed_at),
                }
            )

    daily_rollup: dict[tuple[str, str], dict[str, object]] = {}
    for row in fact_job_lifecycle:
        day = str(row["requested_at"])[:10]
        key = (day, str(row["ai_module_id"]))
        current = daily_rollup.setdefault(
            key,
            {
                "metric_date": day,
                "ai_module_id": row["ai_module_id"],
                "ai_module_name": row["ai_module_name"],
                "job_count": 0,
                "failed_job_count": 0,
                "avg_queue_delay_minutes_total": 0.0,
                "avg_end_to_end_minutes_total": 0.0,
            },
        )
        current["job_count"] = int(current["job_count"]) + 1
        if row["job_final_status"] == "failed":
            current["failed_job_count"] = int(current["failed_job_count"]) + 1
        current["avg_queue_delay_minutes_total"] = float(current["avg_queue_delay_minutes_total"]) + float(row["queue_delay_minutes"])
        current["avg_end_to_end_minutes_total"] = float(current["avg_end_to_end_minutes_total"]) + float(row["end_to_end_minutes"])

    daily_metrics: list[dict[str, object]] = []
    for row in daily_rollup.values():
        job_count = int(row["job_count"])
        failed_job_count = int(row["failed_job_count"])
        daily_metrics.append(
            {
                "metric_date": row["metric_date"],
                "ai_module_id": row["ai_module_id"],
                "ai_module_name": row["ai_module_name"],
                "job_count": job_count,
                "failed_job_count": failed_job_count,
                "failure_rate_pct": round((failed_job_count / job_count) * 100, 2),
                "avg_queue_delay_minutes": round(float(row["avg_queue_delay_minutes_total"]) / job_count, 2),
                "avg_end_to_end_minutes": round(float(row["avg_end_to_end_minutes_total"]) / job_count, 2),
            }
        )

    return {
        "dim_hospital": dim_hospital,
        "dim_disease": dim_disease,
        "dim_ai_module": dim_ai_module,
        "fact_job_lifecycle": fact_job_lifecycle,
        "fact_module_runs": fact_module_runs,
        "daily_metrics": sorted(daily_metrics, key=lambda row: (row["metric_date"], row["ai_module_id"])),
    }


def write_analytics(output_root: Path) -> dict[str, list[dict[str, object]]]:
    paths = build_output_paths(output_root)
    ensure_output_dirs(paths)
    analytics = build_analytics(output_root)
    for table_name, rows in analytics.items():
        _write_csv(paths.analytics_dir / f"{table_name}.csv", rows)
    return analytics


def write_report(output_root: Path) -> str:
    paths = build_output_paths(output_root)
    ensure_output_dirs(paths)
    fact_job_lifecycle = _read_csv(paths.analytics_dir / "fact_job_lifecycle.csv")
    fact_module_runs = _read_csv(paths.analytics_dir / "fact_module_runs.csv")
    report = build_summary_report(fact_job_lifecycle, fact_module_runs)
    report_path = paths.reports_dir / "summary.md"
    report_path.write_text(report, encoding="utf-8")
    copy_manifest = build_copy_manifest(paths.root)
    (paths.reports_dir / "postgres_copy_manifest.sql").write_text(copy_manifest, encoding="utf-8")
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synthetic ETL demo for medical AI workflow observability")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate raw synthetic datasets")
    generate_parser.add_argument("--seed", type=int, default=7)
    generate_parser.add_argument("--requests", type=int, default=120)
    generate_parser.add_argument("--output-root", default="data/generated")

    etl_parser = subparsers.add_parser("etl", help="Build analytics datasets from raw events")
    etl_parser.add_argument("--output-root", default="data/generated")

    report_parser = subparsers.add_parser("report", help="Generate a markdown monitoring summary")
    report_parser.add_argument("--output-root", default="data/generated")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    output_root = Path(args.output_root)

    if args.command == "generate":
        generate_raw(output_root=output_root, request_count=args.requests, seed=args.seed)
        return
    if args.command == "etl":
        write_analytics(output_root=output_root)
        return
    if args.command == "report":
        write_report(output_root=output_root)
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
