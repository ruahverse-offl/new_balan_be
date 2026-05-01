"""
Notification Settings Router
API endpoints for managing notification device settings
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.notification_settings_service import NotificationSettingsService
from app.schemas.notification_settings_schema import (
    NotificationSettingResponse,
    NotificationSettingListResponse,
)
from app.utils.auth import get_current_user_id
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/notification-settings", tags=["Notification Settings"])


@router.get(
    "/",
    response_model=NotificationSettingListResponse,
    summary="List notification device settings",
)
async def list_notification_settings(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    user_id: Optional[UUID] = Query(None),
    device_platform: Optional[str] = Query(None),
    is_push_enabled: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """List all notification device settings with pagination."""
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if device_platform:
        filters["device_platform"] = device_platform
    if is_push_enabled is not None:
        filters["is_push_enabled"] = is_push_enabled
    if is_active is not None:
        filters["is_active"] = is_active

    service = NotificationSettingsService(db)
    return await service.list(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
        filters=filters,
    )


@router.get(
    "/{id}",
    response_model=NotificationSettingResponse,
    summary="Get notification setting by ID",
)
async def get_notification_setting(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Get a specific notification device setting by ID."""
    service = NotificationSettingsService(db)
    result = await service.get_by_id(id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification setting not found",
        )
    return result


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification device setting",
)
async def delete_notification_setting(
    id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Soft delete a notification device setting."""
    service = NotificationSettingsService(db)
    success = await service.delete(id, current_user_id, get_client_ip(request))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification setting not found",
        )
    await db.commit()
    return None
