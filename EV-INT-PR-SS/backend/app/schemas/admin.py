from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"


class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
