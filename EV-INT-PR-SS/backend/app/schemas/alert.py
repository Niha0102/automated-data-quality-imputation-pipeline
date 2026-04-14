from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: str
    user_id: str
    job_id: Optional[str] = None
    type: str
    message: str
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
