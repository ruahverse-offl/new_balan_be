"""
Current-user routes (JWT ``sub``) — e.g. notification inbox for mobile apps.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.db.models import NotificationSetting
from app.services.me_notification_settings_service import MeNotificationSettingsService
from app.services.notification_logs_service import NotificationLogsService
from app.schemas.notification_settings_schema import (
    MeNotificationSettingRegisterRequest,
    MeNotificationSettingRevokeRequest,
    MeNotificationSettingRevokeResponse,
    NotificationSettingResponse,
)
from app.schemas.user_notifications_schema import MyNotificationsResponse
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/api/v1", tags=["me"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "0.0.0.0"
    if request.client:
        return request.client.host
    return "0.0.0.0"


def _notification_setting_to_response(row: NotificationSetting) -> NotificationSettingResponse:
    return NotificationSettingResponse(
        id=row.id,
        user_id=row.user_id,
        device_id=row.device_id,
        device_platform=row.device_platform,
        expo_push_token=row.expo_push_token,
        is_push_enabled=row.is_push_enabled,
        is_active=row.is_active,
        created_by=row.created_by,
        created_at=row.created_at,
        created_ip=row.created_ip,
        updated_by=row.updated_by,
        updated_at=row.updated_at,
        updated_ip=row.updated_ip,
        is_deleted=row.is_deleted,
    )


@router.post(
    "/me/notification-settings",
    response_model=NotificationSettingResponse,
)
async def register_my_notification_device(
    body: MeNotificationSettingRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Register or refresh this device's Expo push token for delivery / customer apps.

    Upserts ``M_notification_settings`` for the JWT user and token so push (e.g. delivery
    assignment) can target this device.
    """
    service = MeNotificationSettingsService(db)
    row = await service.upsert_my_device(current_user_id, body, _client_ip(request))
    await db.commit()
    return _notification_setting_to_response(row)


@router.post(
    "/me/notification-settings/revoke",
    response_model=MeNotificationSettingRevokeResponse,
)
async def revoke_my_notification_devices(
    body: MeNotificationSettingRevokeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Soft-delete this user's notification device rows (call before clearing the client session on logout).

    Identifies rows by ``expo_push_token`` and/or ``device_id`` so pushes stop targeting this install.
    """
    service = MeNotificationSettingsService(db)
    count = await service.revoke_my_devices(current_user_id, body, _client_ip(request))
    await db.commit()
    return MeNotificationSettingRevokeResponse(revoked_count=count)


@router.get("/me/notifications", response_model=MyNotificationsResponse)
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Latest notifications for the signed-in user (max 30), newest first.

    Rows come from ``T_notification_logs`` (push/email send attempts). Title/body are taken
    from the stored ``payload_snapshot`` when present.
    """
    service = NotificationLogsService(db)
    return await service.list_my_notifications(current_user_id)
