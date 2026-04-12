from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class CurrentUserResponse(BaseModel):
    id: int
    subject: str
    username: str
    email: str | None = None
    full_name: str | None = None
    roles: list[str] = Field(default_factory=list)


class JobRunRequest(BaseModel):
    request_count: int = Field(default=120, ge=10, le=1000)
    seed: int = Field(default=7, ge=1, le=999_999)


class PipelineRunResponse(BaseModel):
    id: int
    status: str
    request_count: int
    seed: int
    celery_task_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    triggered_by_username: str | None = None


class ModuleSummary(BaseModel):
    ai_module_name: str
    total_runs: int
    failed_runs: int
    failure_rate_pct: float
    avg_run_duration_minutes: float


class OverviewResponse(BaseModel):
    total_jobs: int
    failed_jobs: int
    avg_request_to_upload_complete_minutes: float
    avg_upload_complete_to_processing_start_minutes: float
    avg_queue_delay_minutes: float
    avg_end_to_end_minutes: float
    latest_run_status: str | None = None
    module_summaries: list[ModuleSummary]
    recent_runs: list[PipelineRunResponse]


class DashboardViewCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    filters_json: dict = Field(default_factory=dict)
    layout_json: dict = Field(default_factory=dict)


class DashboardViewResponse(BaseModel):
    id: int
    name: str
    filters_json: dict
    layout_json: dict
    created_at: datetime
    updated_at: datetime

