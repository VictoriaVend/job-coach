"""Celery app initialization and configuration."""

from celery import Celery

from job_coach.app.core.config import settings

celery_app = Celery(
    "job_coach",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["job_coach.app.tasks.worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
