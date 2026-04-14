"""Reports API — Requirements 9.2, 14.2, 14.4."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models import Job, User
from app.db.mongo import reports_collection
from app.db.postgres import get_db
import app.services.storage as _storage
from app.core.config import settings

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{job_id}")
async def get_report(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the full JSON report for a job. Requirement 9.2."""
    await _verify_job_ownership(job_id, current_user.id, db)
    col = reports_collection()
    try:
        doc = await col.find_one({"_id": job_id})
    except Exception:
        doc = None
    if doc is None:
        raise HTTPException(status_code=404, detail="Report not found")
    doc.pop("_id", None)
    return doc


@router.get("/{job_id}/download")
async def download_report(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a presigned S3 URL for the PDF report. Requirement 14.2, 14.4."""
    await _verify_job_ownership(job_id, current_user.id, db)
    s3_key = f"reports/{job_id}/report.pdf"
    url = _storage.generate_presigned_url(settings.S3_REPORTS_BUCKET, s3_key)
    return {"download_url": url, "expires_in": 3600}


async def _verify_job_ownership(job_id: str, user_id: str, db: AsyncSession):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return job
