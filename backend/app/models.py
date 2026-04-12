from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AppUser(Base):
    __tablename__ = "app_user"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_subject: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    pipeline_runs: Mapped[list["PipelineRun"]] = relationship(back_populates="triggered_by")
    dashboard_views: Mapped[list["DashboardView"]] = relationship(back_populates="owner")


class PipelineRun(Base):
    __tablename__ = "pipeline_run"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    triggered_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("app.app_user.id"), nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    request_count: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    triggered_by: Mapped[AppUser | None] = relationship(back_populates="pipeline_runs")


class DashboardView(Base):
    __tablename__ = "dashboard_view"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app.app_user.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    filters_json: Mapped[dict] = mapped_column(JSON)
    layout_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner: Mapped[AppUser] = relationship(back_populates="dashboard_views")

