"""
Notification Master Router
API endpoints for managing notification templates
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.notification_master_service import NotificationMasterService
from app.schemas.notification_master_schema import (
    NotificationMasterCreateRequest,
    NotificationMasterUpdateRequest,
    NotificationMasterResponse,
    NotificationMasterListResponse,
)
from app.utils.auth import get_current_user_id
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/notification-master", tags=["Notification Master"])


@router.post(
    "/",
    response_model=NotificationMasterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create notification master template",
)
async def create_notification_master(
    request_data: NotificationMasterCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Create a new notification master template."""
    service = NotificationMasterService(db)
    result = await service.create(request_data, current_user_id, get_client_ip(request))
    await db.commit()
    return result


@router.get(
    "/",
    response_model=NotificationMasterListResponse,
    summary="List notification master templates",
)
async def list_notification_masters(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    event_code: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """List all notification master templates with pagination."""
    filters = {}
    if event_code:
        filters["event_code"] = event_code
    if is_active is not None:
        filters["is_active"] = is_active

    service = NotificationMasterService(db)
    return await service.list(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
        filters=filters,
    )


@router.get(
    "/{id}",
    response_model=NotificationMasterResponse,
    summary="Get notification master by ID",
)
async def get_notification_master(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Get a specific notification master template by ID."""
    service = NotificationMasterService(db)
    result = await service.get_by_id(id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification master not found",
        )
    return result


@router.patch(
    "/{id}",
    response_model=NotificationMasterResponse,
    summary="Update notification master template",
)
async def update_notification_master(
    id: UUID,
    request_data: NotificationMasterUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Update an existing notification master template."""
    service = NotificationMasterService(db)
    result = await service.update(id, request_data, current_user_id, get_client_ip(request))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification master not found",
        )
    await db.commit()
    return result


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification master template",
)
async def delete_notification_master(
    id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Soft delete a notification master template."""
    service = NotificationMasterService(db)
    success = await service.delete(id, current_user_id, get_client_ip(request))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification master not found",
        )
    await db.commit()
    return None
