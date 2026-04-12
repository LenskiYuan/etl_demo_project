from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from .celery_app import celery_app
from .database_init import initialize_database
from .db import SessionLocal
from .etl_runner import run_pipeline_snapshot
from .models import PipelineRun


@celery_app.task(name="backend.app.tasks.run_pipeline_task")
def run_pipeline_task(run_id: int, request_count: int, seed: int) -> None:
    initialize_database()
    session = SessionLocal()
    try:
        pipeline_run = session.scalar(select(PipelineRun).where(PipelineRun.id == run_id))
        if pipeline_run is None:
            return

        pipeline_run.status = "running"
        pipeline_run.started_at = datetime.now(timezone.utc)
        pipeline_run.error_message = None
        session.commit()

        run_pipeline_snapshot(request_count=request_count, seed=seed)

        pipeline_run.status = "succeeded"
        pipeline_run.finished_at = datetime.now(timezone.utc)
        session.commit()
    except Exception as exc:
        session.rollback()
        pipeline_run = session.scalar(select(PipelineRun).where(PipelineRun.id == run_id))
        if pipeline_run is not None:
            pipeline_run.status = "failed"
            pipeline_run.finished_at = datetime.now(timezone.utc)
            pipeline_run.error_message = str(exc)
            session.commit()
        raise
    finally:
        session.close()

