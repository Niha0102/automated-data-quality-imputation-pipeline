"""ML Pipeline package — Celery worker entry point."""
from celery import Celery
import os

celery_app = Celery(
    "adqip_pipeline",
    broker=os.getenv("CELERY_BROKER_URL", "redis://:adqip_secret@localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://:adqip_secret@localhost:6379/1"),
    include=["pipeline.tasks"],
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
