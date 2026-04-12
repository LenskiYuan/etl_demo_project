from __future__ import annotations

from celery import Celery

from .config import get_settings


settings = get_settings()

celery_app = Celery("etl_demo", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600
celery_app.conf.imports = ("backend.app.tasks",)
