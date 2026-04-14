import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.security import hash_password
from app.db.models import User
from app.db.postgres import get_db
from app.schemas.admin import (
    AdminUserCreate, AdminUserListResponse,
    AdminUserResponse, AdminUserUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_ROLES = {"user", "admin"}


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),  # enforces Admin role — Req 1.5
):
    total = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    return AdminUserListResponse(items=list(result.scalars().all()), total=total)


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create a new user — Requirement 1.6."""
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"Invalid role. Must be one of: {VALID_ROLES}")

    existing = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    body: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Update role or active status — Requirement 1.6."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        if body.role not in VALID_ROLES:
            raise HTTPException(status_code=422, detail=f"Invalid role. Must be one of: {VALID_ROLES}")
        user.role = body.role

    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return user
