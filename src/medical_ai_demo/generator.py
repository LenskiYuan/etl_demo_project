from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import random


HOSPITALS = [
    {"hospital_id": "H001", "hospital_name": "North Harbor Medical Center", "region": "Northeast"},
    {"hospital_id": "H002", "hospital_name": "Sunrise Valley Hospital", "region": "South"},
    {"hospital_id": "H003", "hospital_name": "Westlake Imaging Institute", "region": "West"},
    {"hospital_id": "H004", "hospital_name": "Riverbend General", "region": "Midwest"},
]

DISEASE_MODULES = {
    "brain_tumor": {"ai_module_id": "MOD-BRAIN-01", "ai_module_name": "NeuroSight", "base_minutes": 42},
    "breast_tumor": {"ai_module_id": "MOD-BREAST-01", "ai_module_name": "MammoMap", "base_minutes": 34},
    "cteph": {"ai_module_id": "MOD-CTEPH-01", "ai_module_name": "PulmoFlow", "base_minutes": 57},
}

ERROR_CATEGORIES = ["docker_timeout", "model_runtime_error", "input_validation", "capacity_exhausted"]


@dataclass(frozen=True)
class DemoData:
    requests: list[dict[str, object]]
    image_upload_events: list[dict[str, object]]
    processing_jobs: list[dict[str, object]]
    module_runs: list[dict[str, object]]
    job_status_events: list[dict[str, object]]


def _iso(ts: datetime) -> str:
    return ts.isoformat(timespec="seconds")


def _weighted_choice(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.42:
        return "brain_tumor"
    if roll < 0.77:
        return "breast_tumor"
    return "cteph"


def generate_demo_data(request_count: int = 120, seed: int = 7) -> DemoData:
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, 8, 0, 0)

    requests: list[dict[str, object]] = []
    image_upload_events: list[dict[str, object]] = []
    processing_jobs: list[dict[str, object]] = []
    module_runs: list[dict[str, object]] = []
    job_status_events: list[dict[str, object]] = []

    for index in range(request_count):
        request_id = f"REQ-{index + 1:05d}"
        hospital = rng.choice(HOSPITALS)
        disease = _weighted_choice(rng)
        module = DISEASE_MODULES[disease]

        requested_at = start + timedelta(minutes=(index * 79) + rng.randint(0, 35))
        expected_images = rng.randint(3, 8)

        requests.append(
            {
                "request_id": request_id,
                "hospital_id": hospital["hospital_id"],
                "disease_type": disease,
                "priority": "urgent" if rng.random() < 0.18 else "standard",
                "requested_at": _iso(requested_at),
                "expected_image_count": expected_images,
            }
        )

        last_upload_at = requested_at
        for image_number in range(1, expected_images + 1):
            upload_gap = rng.randint(3, 18) + (image_number // 3)
            uploaded_at = last_upload_at + timedelta(minutes=upload_gap)
            last_upload_at = uploaded_at
            image_upload_events.append(
                {
                    "upload_event_id": f"UP-{request_id}-{image_number:02d}",
                    "request_id": request_id,
                    "image_id": f"IMG-{request_id}-{image_number:02d}",
                    "uploaded_at": _iso(uploaded_at),
                    "storage_bucket": "synthetic-medical-ai-input",
                }
            )

        queued_at = last_upload_at + timedelta(minutes=rng.randint(1, 12))
        queue_delay_minutes = rng.randint(4, 35)
        if rng.random() < 0.12:
            queue_delay_minutes += rng.randint(20, 90)
        started_at = queued_at + timedelta(minutes=queue_delay_minutes)

        should_retry = rng.random() < 0.16
        failure_after_retry = rng.random() < 0.35 if should_retry else rng.random() < 0.09

        attempt_count = 2 if should_retry else 1
        final_status = "failed" if failure_after_retry else "succeeded"

        job_id = f"JOB-{index + 1:05d}"
        processing_jobs.append(
            {
                "job_id": job_id,
                "request_id": request_id,
                "ai_module_id": module["ai_module_id"],
                "queued_at": _iso(queued_at),
                "final_status": final_status,
                "attempt_count": attempt_count,
            }
        )

        job_status_events.append(
            {
                "job_status_event_id": f"JSE-{job_id}-01",
                "job_id": job_id,
                "request_id": request_id,
                "event_type": "queued",
                "event_time": _iso(queued_at),
                "event_detail": "uploads_complete",
            }
        )

        current_start = started_at
        for attempt in range(1, attempt_count + 1):
            duration_minutes = max(12, int(rng.gauss(module["base_minutes"], 8)))
            run_completed_at = current_start + timedelta(minutes=duration_minutes)
            is_last_attempt = attempt == attempt_count
            run_status = "failed" if (attempt == 1 and should_retry) or (is_last_attempt and final_status == "failed") else "succeeded"

            error_category = ""
            if run_status == "failed":
                error_category = rng.choice(ERROR_CATEGORIES)

            run_id = f"RUN-{job_id}-{attempt:02d}"
            module_runs.append(
                {
                    "run_id": run_id,
                    "job_id": job_id,
                    "request_id": request_id,
                    "ai_module_id": module["ai_module_id"],
                    "attempt_number": attempt,
                    "started_at": _iso(current_start),
                    "completed_at": _iso(run_completed_at),
                    "run_status": run_status,
                    "error_category": error_category,
                }
            )

            job_status_events.append(
                {
                    "job_status_event_id": f"JSE-{job_id}-{attempt * 2:02d}",
                    "job_id": job_id,
                    "request_id": request_id,
                    "event_type": "started",
                    "event_time": _iso(current_start),
                    "event_detail": f"attempt_{attempt}",
                }
            )

            if run_status == "failed" and not is_last_attempt:
                retry_delay = rng.randint(6, 25)
                retry_at = run_completed_at + timedelta(minutes=retry_delay)
                job_status_events.append(
                    {
                        "job_status_event_id": f"JSE-{job_id}-{attempt * 2 + 1:02d}",
                        "job_id": job_id,
                        "request_id": request_id,
                        "event_type": "retry_scheduled",
                        "event_time": _iso(retry_at),
                        "event_detail": error_category,
                    }
                )
                current_start = retry_at
                continue

            final_event = "failed" if run_status == "failed" else "succeeded"
            job_status_events.append(
                {
                    "job_status_event_id": f"JSE-{job_id}-{attempt * 2 + 1:02d}",
                    "job_id": job_id,
                    "request_id": request_id,
                    "event_type": final_event,
                    "event_time": _iso(run_completed_at),
                    "event_detail": error_category or "complete",
                }
            )

    return DemoData(
        requests=requests,
        image_upload_events=image_upload_events,
        processing_jobs=processing_jobs,
        module_runs=module_runs,
        job_status_events=job_status_events,
    )

