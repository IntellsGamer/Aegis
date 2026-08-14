"""Celery worker entry point (Flask app context aware)."""
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "aegis",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
)


def create_flask_app():
    from app import create_app

    return create_app()
