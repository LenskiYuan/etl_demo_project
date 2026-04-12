from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database_init import initialize_database
from .db import SessionLocal, get_db
from .models import AppUser, DashboardView, PipelineRun
from .schemas import (
    CurrentUserResponse,
    DashboardViewCreateRequest,
    DashboardViewResponse,
    JobRunRequest,
    ModuleSummary,
    OverviewResponse,
    PipelineRunResponse,
)
from .security import UserPrincipal, get_current_principal, require_roles
from .tasks import run_pipeline_task


settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    initialize_database()
    _recover_stale_runs()


def _recover_stale_runs() -> None:
    stale_before = datetime.now(timezone.utc) - timedelta(minutes=settings.stale_run_timeout_minutes)
    with SessionLocal() as db:
        db.execute(
            text(
                """
                UPDATE app.pipeline_run
                SET
                    status = 'failed',
                    error_message = COALESCE(
                        error_message,
                        'Marked failed during startup recovery after exceeding the pending/running timeout.'
                    ),
                    finished_at = COALESCE(finished_at, NOW())
                WHERE status IN ('pending', 'running')
                  AND created_at < :stale_before
                """
            ),
            {"stale_before": stale_before},
        )
        db.commit()


def _upsert_app_user(db: Session, principal: UserPrincipal) -> AppUser:
    app_user = db.scalar(select(AppUser).where(AppUser.external_subject == principal.subject))
    if app_user is None:
        app_user = AppUser(
            external_subject=principal.subject,
            username=principal.username,
            email=principal.email,
            full_name=principal.full_name,
        )
        db.add(app_user)
    else:
        app_user.username = principal.username
        app_user.email = principal.email
        app_user.full_name = principal.full_name
    db.commit()
    db.refresh(app_user)
    return app_user


def _serialize_run(row) -> PipelineRunResponse:
    return PipelineRunResponse(
        id=row.id,
        status=row.status,
        request_count=row.request_count,
        seed=row.seed,
        celery_task_id=row.celery_task_id,
        error_message=row.error_message,
        created_at=row.created_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
        triggered_by_username=getattr(row, "triggered_by_username", None),
    )


def _recent_runs(db: Session, limit: int = 8) -> list[PipelineRunResponse]:
    rows = db.execute(
        text(
            """
            SELECT
                pr.id,
                pr.status,
                pr.request_count,
                pr.seed,
                pr.celery_task_id,
                pr.error_message,
                pr.created_at,
                pr.started_at,
                pr.finished_at,
                au.username AS triggered_by_username
            FROM app.pipeline_run pr
            LEFT JOIN app.app_user au ON au.id = pr.triggered_by_user_id
            ORDER BY pr.created_at DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings()
    return [PipelineRunResponse(**row) for row in rows]


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/me", response_model=CurrentUserResponse)
def current_user(
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> CurrentUserResponse:
    app_user = _upsert_app_user(db, principal)
    return CurrentUserResponse(
        id=app_user.id,
        subject=principal.subject,
        username=app_user.username,
        email=app_user.email,
        full_name=app_user.full_name,
        roles=principal.roles,
    )


@app.get("/api/overview", response_model=OverviewResponse)
def overview(
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> OverviewResponse:
    _upsert_app_user(db, principal)
    aggregate_row = db.execute(
        text(
            """
            SELECT
                COUNT(*)::int AS total_jobs,
                COALESCE(SUM(CASE WHEN job_final_status = 'failed' THEN 1 ELSE 0 END), 0)::int AS failed_jobs,
                COALESCE(AVG(request_to_upload_complete_minutes), 0)::float AS avg_request_to_upload_complete_minutes,
                COALESCE(AVG(upload_complete_to_processing_start_minutes), 0)::float AS avg_upload_complete_to_processing_start_minutes,
                COALESCE(AVG(queue_delay_minutes), 0)::float AS avg_queue_delay_minutes,
                COALESCE(AVG(end_to_end_minutes), 0)::float AS avg_end_to_end_minutes
            FROM analytics.fact_job_lifecycle
            """
        )
    ).mappings().one()

    module_rows = db.execute(
        text(
            """
            SELECT
                ai_module_name,
                COUNT(*)::int AS total_runs,
                COUNT(*) FILTER (WHERE run_status = 'failed')::int AS failed_runs,
                ROUND(
                    100.0 * COUNT(*) FILTER (WHERE run_status = 'failed') / NULLIF(COUNT(*), 0),
                    2
                )::float AS failure_rate_pct,
                COALESCE(AVG(run_duration_minutes), 0)::float AS avg_run_duration_minutes
            FROM analytics.fact_module_runs
            GROUP BY ai_module_name
            ORDER BY failure_rate_pct DESC, ai_module_name ASC
            """
        )
    ).mappings()

    latest_run_status = db.execute(
        text("SELECT status FROM app.pipeline_run ORDER BY created_at DESC LIMIT 1")
    ).scalar_one_or_none()

    return OverviewResponse(
        total_jobs=aggregate_row["total_jobs"],
        failed_jobs=aggregate_row["failed_jobs"],
        avg_request_to_upload_complete_minutes=round(aggregate_row["avg_request_to_upload_complete_minutes"], 2),
        avg_upload_complete_to_processing_start_minutes=round(
            aggregate_row["avg_upload_complete_to_processing_start_minutes"],
            2,
        ),
        avg_queue_delay_minutes=round(aggregate_row["avg_queue_delay_minutes"], 2),
        avg_end_to_end_minutes=round(aggregate_row["avg_end_to_end_minutes"], 2),
        latest_run_status=latest_run_status,
        module_summaries=[ModuleSummary(**row) for row in module_rows],
        recent_runs=_recent_runs(db),
    )


@app.get("/api/jobs", response_model=list[PipelineRunResponse])
def list_jobs(
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> list[PipelineRunResponse]:
    _upsert_app_user(db, principal)
    return _recent_runs(db, limit=25)


@app.post("/api/jobs/run", response_model=PipelineRunResponse)
def trigger_job(
    payload: JobRunRequest,
    principal: UserPrincipal = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> PipelineRunResponse:
    app_user = _upsert_app_user(db, principal)

    pipeline_run = PipelineRun(
        triggered_by_user_id=app_user.id,
        status="pending",
        request_count=payload.request_count,
        seed=payload.seed,
    )
    db.add(pipeline_run)
    db.commit()
    db.refresh(pipeline_run)

    async_result = run_pipeline_task.delay(pipeline_run.id, payload.request_count, payload.seed)
    pipeline_run.celery_task_id = async_result.id
    db.commit()
    db.refresh(pipeline_run)

    return PipelineRunResponse(
        id=pipeline_run.id,
        status=pipeline_run.status,
        request_count=pipeline_run.request_count,
        seed=pipeline_run.seed,
        celery_task_id=pipeline_run.celery_task_id,
        error_message=pipeline_run.error_message,
        created_at=pipeline_run.created_at,
        started_at=pipeline_run.started_at,
        finished_at=pipeline_run.finished_at,
        triggered_by_username=app_user.username,
    )


@app.get("/api/jobs/{run_id}", response_model=PipelineRunResponse)
def get_job(
    run_id: int,
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> PipelineRunResponse:
    _upsert_app_user(db, principal)
    row = db.execute(
        text(
            """
            SELECT
                pr.id,
                pr.status,
                pr.request_count,
                pr.seed,
                pr.celery_task_id,
                pr.error_message,
                pr.created_at,
                pr.started_at,
                pr.finished_at,
                au.username AS triggered_by_username
            FROM app.pipeline_run pr
            LEFT JOIN app.app_user au ON au.id = pr.triggered_by_user_id
            WHERE pr.id = :run_id
            """
        ),
        {"run_id": run_id},
    ).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return PipelineRunResponse(**row)


@app.get("/api/views", response_model=list[DashboardViewResponse])
def list_dashboard_views(
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> list[DashboardViewResponse]:
    app_user = _upsert_app_user(db, principal)
    rows = db.scalars(
        select(DashboardView).where(DashboardView.user_id == app_user.id).order_by(DashboardView.updated_at.desc())
    ).all()
    return [
        DashboardViewResponse(
            id=row.id,
            name=row.name,
            filters_json=row.filters_json,
            layout_json=row.layout_json,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@app.post("/api/views", response_model=DashboardViewResponse)
def create_dashboard_view(
    payload: DashboardViewCreateRequest,
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> DashboardViewResponse:
    app_user = _upsert_app_user(db, principal)
    view = DashboardView(
        user_id=app_user.id,
        name=payload.name,
        filters_json=payload.filters_json,
        layout_json=payload.layout_json,
    )
    db.add(view)
    db.commit()
    db.refresh(view)
    return DashboardViewResponse(
        id=view.id,
        name=view.name,
        filters_json=view.filters_json,
        layout_json=view.layout_json,
        created_at=view.created_at,
        updated_at=view.updated_at,
    )
