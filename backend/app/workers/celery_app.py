"""Celery application instance for background ingestion & indexing jobs.

Referenced by docker-compose as ``celery -A app.workers.celery_app worker``.
Uses Redis (see ``settings.REDIS_URL``) as both broker and result backend.
Task modules (e.g. ``app.workers.tasks``) are auto-discovered once added.
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "knowledgehub",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Discover tasks in app.workers.tasks (and submodules) when they are created.
celery_app.autodiscover_tasks(["app.workers"])
