from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DatasetResponse(BaseModel):
    id: str
    name: str
    format: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    file_path: Optional[str] = None
    is_baseline: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    total: int


class DatasetVersionResponse(BaseModel):
    id: str
    dataset_id: str
    version_number: int
    job_id: Optional[str] = None
    file_path: str
    quality_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    items: list["JobResponse"]
    total: int


class JobSubmitRequest(BaseModel):
    dataset_id: str
    pipeline_config: dict = {}
    nl_query: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    dataset_id: str
    user_id: str
    status: str
    progress: int
    pipeline_config: dict
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobStatusResponse(BaseModel):
    id: str
    status: str
    progress: int
    error_message: Optional[str] = None
