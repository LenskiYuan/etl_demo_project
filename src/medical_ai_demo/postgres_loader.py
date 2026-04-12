from __future__ import annotations

from pathlib import Path


RAW_TABLES = [
    "requests",
    "image_upload_events",
    "processing_jobs",
    "module_runs",
    "job_status_events",
]

ANALYTICS_TABLES = [
    "dim_hospital",
    "dim_disease",
    "dim_ai_module",
    "fact_job_lifecycle",
    "fact_module_runs",
    "daily_metrics",
]


def build_copy_manifest(output_root: Path | str) -> str:
    root = Path(output_root)
    statements = []
    for table_name in RAW_TABLES:
        statements.append(
            f"\\copy raw.{table_name} FROM '{(root / 'raw' / f'{table_name}.csv').resolve()}' CSV HEADER;"
        )
    for table_name in ANALYTICS_TABLES:
        statements.append(
            f"\\copy analytics.{table_name} FROM '{(root / 'analytics' / f'{table_name}.csv').resolve()}' CSV HEADER;"
        )
    return "\n".join(statements)

