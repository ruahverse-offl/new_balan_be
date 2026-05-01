"""
Admin test push — POST to send an Expo notification to devices registered for a user.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.schemas.notification_test_push_schema import (
    NotificationTestPushRequest,
    NotificationTestPushResponse,
    NotificationTestPushResultItem,
)
from app.services.notification_test_push_service import NotificationTestPushService
from app.utils.rbac import require_any_module_action

router = APIRouter(prefix="/api/v1/notification-test", tags=["Notification Test"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "0.0.0.0"
    if request.client:
        return request.client.host
    return "0.0.0.0"


@router.post(
    "/send",
    response_model=NotificationTestPushResponse,
    status_code=status.HTTP_200_OK,
    summary="Send test push notification to a user (Expo)",
)
async def send_test_push(
    body: NotificationTestPushRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(
        require_any_module_action(
            [
                ("notification-settings", "update"),
                ("notification-master", "update"),
                ("notification-logs", "read"),
            ]
        ),
    ),
):
    """
    Delivers a test push via Expo to every push-enabled ``M_notification_settings`` row for ``userId``.

    Caller must have at least one of: **notification-settings** update, **notification-master** update,
    or **notification-logs** read (typical ADMIN / MANAGER staff). ``DEV_ADMIN`` only has RBAC modules,
    so use an ``ADMIN``/``MANAGER`` token—or grant one of those permissions via the RBAC matrix.

    Optional **androidChannelId**: set to ``delivery_default`` when testing the delivery partner Android app.
    """
    service = NotificationTestPushService(db)
    messages_count, raw = await service.send_to_user(
        target_user_id=body.user_id,
        title=body.title,
        body=body.body,
        android_channel_id=body.android_channel_id,
        audit_user_id=current_user_id,
        audit_ip=_client_ip(request),
    )
    await db.commit()
    results = [
        NotificationTestPushResultItem(
            expo_push_token=r.get("expo_push_token") or "",
            status=str(r.get("status") or "error"),
            detail=r.get("detail"),
        )
        for r in raw
    ]
    return NotificationTestPushResponse(
        user_id=body.user_id,
        tokens_targeted=messages_count,
        results=results,
    )
