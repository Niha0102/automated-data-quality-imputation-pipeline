"""Pipeline Celery task — full orchestration implemented in Task 15."""
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="pipeline.run")
def run_pipeline(self, job_id: str, dataset_id: str, user_id: str, pipeline_config: dict):
    """Placeholder — full implementation in Task 15."""
    # Will be replaced with full 12-stage pipeline in Task 15.1
    return {"job_id": job_id, "status": "PENDING"}
