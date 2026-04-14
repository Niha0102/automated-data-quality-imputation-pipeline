import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.models import Dataset, DatasetVersion, User
from app.db.postgres import get_db
from app.schemas.dataset import (
    DatasetListResponse, DatasetResponse, DatasetVersionResponse
)
import app.services.storage as _storage

router = APIRouter(prefix="/datasets", tags=["datasets"])

SUPPORTED_FORMATS = {"csv", "json", "xlsx"}
CONTENT_TYPES = {
    "csv": "text/csv",
    "json": "application/json",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


# ── POST /datasets ─────────────────────────────────────────────────────────────

@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate format (requirement 2.5)
    ext = _get_extension(file.filename or "")
    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file format '.{ext}'. Supported formats: {sorted(SUPPORTED_FORMATS)}",
        )

    # Read and validate size (requirement 2.4)
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {len(data):,} bytes exceeds the 2 GB limit.",
        )

    # Upload to S3/MinIO
    dataset_id = str(uuid.uuid4())
    s3_key = f"raw/{current_user.id}/{dataset_id}/{file.filename}"
    await _storage.upload_file(settings.S3_DATASETS_BUCKET, s3_key, data, CONTENT_TYPES.get(ext, "application/octet-stream"))

    # Persist metadata (requirement 2.8)
    dataset = Dataset(
        id=dataset_id,
        user_id=current_user.id,
        name=file.filename or dataset_id,
        format=ext,
        file_path=s3_key,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


# ── GET /datasets ──────────────────────────────────────────────────────────────

@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_result = await db.execute(
        select(func.count()).select_from(Dataset).where(Dataset.user_id == current_user.id)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(Dataset.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return DatasetListResponse(items=list(items), total=total)


# ── GET /datasets/{id} ─────────────────────────────────────────────────────────

@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = await _get_owned_dataset(dataset_id, current_user.id, db)
    return dataset


# ── DELETE /datasets/{id} ──────────────────────────────────────────────────────

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = await _get_owned_dataset(dataset_id, current_user.id, db)
    if dataset.file_path:
        await _storage.delete_file(settings.S3_DATASETS_BUCKET, dataset.file_path)
    await db.delete(dataset)
    await db.commit()


# ── GET /datasets/{id}/versions ────────────────────────────────────────────────

@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionResponse])
async def list_versions(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_dataset(dataset_id, current_user.id, db)
    result = await db.execute(
        select(DatasetVersion)
        .where(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.asc())
    )
    return result.scalars().all()


# ── POST /datasets/{id}/baseline ───────────────────────────────────────────────

@router.post("/{dataset_id}/baseline", response_model=DatasetResponse)
async def set_baseline(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Clear existing baseline for this user
    existing = await db.execute(
        select(Dataset).where(Dataset.user_id == current_user.id, Dataset.is_baseline == True)  # noqa: E712
    )
    for ds in existing.scalars().all():
        ds.is_baseline = False

    dataset = await _get_owned_dataset(dataset_id, current_user.id, db)
    dataset.is_baseline = True
    await db.commit()
    await db.refresh(dataset)
    return dataset


# ── GET /datasets/{id}/download ────────────────────────────────────────────────

@router.get("/{dataset_id}/download")
async def download_dataset(
    dataset_id: str,
    format: Literal["csv", "xlsx", "json"] = Query("csv"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a presigned S3 URL for the latest cleaned version of the dataset."""
    await _get_owned_dataset(dataset_id, current_user.id, db)

    # Find latest version with the requested format
    result = await db.execute(
        select(DatasetVersion)
        .where(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
        .limit(1)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="No processed version available yet")

    # Derive the format-specific S3 key (pipeline writes csv/xlsx/json variants)
    base_key = version.file_path.rsplit(".", 1)[0]
    s3_key = f"{base_key}.{format}"
    url = _storage.generate_presigned_url(settings.S3_DATASETS_BUCKET, s3_key)
    return {"download_url": url, "format": format, "expires_in": 3600}


# ── Helper ─────────────────────────────────────────────────────────────────────

async def _get_owned_dataset(dataset_id: str, user_id: str, db: AsyncSession) -> Dataset:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")  # requirement 1.7
    return dataset
