import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models import Dataset, Job, User
from app.db.postgres import get_db
from app.db.redis import cache_get
from app.schemas.dataset import JobResponse, JobStatusResponse, JobSubmitRequest, JobListResponse
from app.tasks.pipeline_task import run_pipeline

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import func as sqlfunc
    total_result = await db.execute(
        select(sqlfunc.count()).select_from(Job).where(Job.user_id == current_user.id)
    )
    total = total_result.scalar_one()
    result = await db.execute(
        select(Job)
        .where(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return JobListResponse(items=list(items), total=total)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def submit_job(
    body: JobSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify dataset ownership
    result = await db.execute(select(Dataset).where(Dataset.id == body.dataset_id))
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    # Merge nl_query into pipeline_config if provided
    config = dict(body.pipeline_config)
    if body.nl_query:
        config["nl_query"] = body.nl_query

    job = Job(
        id=str(uuid.uuid4()),
        dataset_id=body.dataset_id,
        user_id=current_user.id,
        status="PENDING",
        pipeline_config=config,
        progress=0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Enqueue Celery task — returns immediately (requirement 2.8)
    run_pipeline.delay(job.id, body.dataset_id, current_user.id, config)

    return job


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await _get_owned_job(job_id, current_user.id, db)
    return job


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await _get_owned_job(job_id, current_user.id, db)

    # Check Redis cache for live progress (updated by worker)
    cached_progress = await cache_get(f"job_status:{job_id}")
    progress = int(cached_progress) if cached_progress is not None else job.progress

    return JobStatusResponse(
        id=job.id,
        status=job.status,
        progress=progress,
        error_message=job.error_message,
    )


async def _get_owned_job(job_id: str, user_id: str, db: AsyncSession) -> Job:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return job
