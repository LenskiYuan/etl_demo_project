from __future__ import annotations

import csv
import tempfile
from pathlib import Path
import unittest

from medical_ai_demo.pipeline import generate_raw, write_analytics, write_report


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PipelineTestCase(unittest.TestCase):
    def test_end_to_end_pipeline_outputs_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            generate_raw(output_root=output_root, request_count=25, seed=11)
            analytics = write_analytics(output_root=output_root)
            report = write_report(output_root=output_root)

            self.assertEqual(len(analytics["fact_job_lifecycle"]), 25)
            self.assertIn("# Observability Summary", report)
            self.assertTrue((output_root / "raw" / "requests.csv").exists())
            self.assertTrue((output_root / "analytics" / "fact_job_lifecycle.csv").exists())
            self.assertTrue((output_root / "reports" / "summary.md").exists())

    def test_lifecycle_metrics_are_non_negative(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            generate_raw(output_root=output_root, request_count=40, seed=5)
            write_analytics(output_root=output_root)

            lifecycle_rows = _read_csv(output_root / "analytics" / "fact_job_lifecycle.csv")
            self.assertTrue(lifecycle_rows)

            for row in lifecycle_rows:
                self.assertGreaterEqual(float(row["request_to_upload_complete_minutes"]), 0.0)
                self.assertGreaterEqual(float(row["upload_complete_to_processing_start_minutes"]), 0.0)
                self.assertGreaterEqual(float(row["queue_delay_minutes"]), 0.0)
                self.assertGreaterEqual(float(row["end_to_end_minutes"]), 0.0)

    def test_retry_jobs_create_multiple_module_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            generate_raw(output_root=output_root, request_count=80, seed=17)
            write_analytics(output_root=output_root)

            lifecycle_rows = _read_csv(output_root / "analytics" / "fact_job_lifecycle.csv")
            run_rows = _read_csv(output_root / "analytics" / "fact_module_runs.csv")
            retried_jobs = {row["job_id"] for row in lifecycle_rows if int(row["attempt_count"]) > 1}
            self.assertTrue(retried_jobs)

            run_counts: dict[str, int] = {}
            for row in run_rows:
                run_counts[row["job_id"]] = run_counts.get(row["job_id"], 0) + 1

            for job_id in retried_jobs:
                self.assertGreaterEqual(run_counts.get(job_id, 0), 2)


if __name__ == "__main__":
    unittest.main()
