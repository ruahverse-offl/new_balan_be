"""
Notification Logs Router
API endpoints for viewing notification logs
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.notification_logs_admin_service import NotificationLogsAdminService
from app.schemas.notification_logs_schema import (
    NotificationLogResponse,
    NotificationLogListResponse,
)
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/api/v1/notification-logs", tags=["Notification Logs"])


@router.get(
    "/",
    response_model=NotificationLogListResponse,
    summary="List notification logs",
)
async def list_notification_logs(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    user_id: Optional[UUID] = Query(None),
    send_status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """List all notification logs with pagination."""
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if send_status:
        filters["send_status"] = send_status
    if channel:
        filters["channel"] = channel

    service = NotificationLogsAdminService(db)
    return await service.list(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
        filters=filters,
    )


@router.get(
    "/{id}",
    response_model=NotificationLogResponse,
    summary="Get notification log by ID",
)
async def get_notification_log(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Get a specific notification log by ID."""
    service = NotificationLogsAdminService(db)
    result = await service.get_by_id(id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification log not found",
        )
    return result
