from __future__ import annotations

from pathlib import Path
import tempfile

import psycopg

from medical_ai_demo.pipeline import generate_raw, write_analytics, write_report

from .config import get_settings


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


def _copy_csv_to_table(cursor: psycopg.Cursor, csv_path: Path, qualified_table: str) -> None:
    with csv_path.open("r", encoding="utf-8") as handle:
        with cursor.copy(f"COPY {qualified_table} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)") as copy:
            while True:
                chunk = handle.read(8192)
                if not chunk:
                    break
                copy.write(chunk)


def run_pipeline_snapshot(request_count: int, seed: int) -> None:
    settings = get_settings()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_root = Path(tmpdir)
        generate_raw(output_root=output_root, request_count=request_count, seed=seed)
        write_analytics(output_root=output_root)
        write_report(output_root=output_root)

        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                for table_name in reversed(ANALYTICS_TABLES):
                    cursor.execute(f"TRUNCATE TABLE analytics.{table_name} RESTART IDENTITY CASCADE")
                for table_name in reversed(RAW_TABLES):
                    cursor.execute(f"TRUNCATE TABLE raw.{table_name} RESTART IDENTITY CASCADE")

                for table_name in RAW_TABLES:
                    _copy_csv_to_table(cursor, output_root / "raw" / f"{table_name}.csv", f"raw.{table_name}")
                for table_name in ANALYTICS_TABLES:
                    _copy_csv_to_table(cursor, output_root / "analytics" / f"{table_name}.csv", f"analytics.{table_name}")

            connection.commit()

