"""Celery app for the ML pipeline worker."""
from pipeline import celery_app  # re-export from package __init__

__all__ = ["celery_app"]
