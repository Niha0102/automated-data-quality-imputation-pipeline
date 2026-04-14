from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models import Alert, User
from app.db.postgres import get_db
from app.schemas.alert import AlertListResponse, AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    resolved: bool = Query(False, description="Include resolved alerts"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return active (or all) alerts for the current user — Requirement 16.3."""
    query = select(Alert).where(Alert.user_id == current_user.id)
    if not resolved:
        query = query.where(Alert.is_resolved == False)  # noqa: E712

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar_one()

    result = await db.execute(
        query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()
    return AlertListResponse(items=list(items), total=total)


@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an alert as resolved — Requirement 16.4."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    alert.is_resolved = True
    await db.commit()
    await db.refresh(alert)
    return alert
