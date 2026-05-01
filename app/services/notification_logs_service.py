"""
Notification logs — read paths for the current user's inbox.
"""

import json
import logging
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notification_logs_repository import NotificationLogsRepository
from app.schemas.user_notifications_schema import MyNotificationItem, MyNotificationsResponse

logger = logging.getLogger(__name__)

_MY_NOTIFICATIONS_MAX = 30


def _parse_payload_snapshot(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _title_body_from_payload(payload: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    title = (payload.get("title") or payload.get("subject") or "").strip()
    body = payload.get("body")
    if body is not None and not isinstance(body, str):
        body = str(body)
    body = (body or "").strip() or None
    if not title:
        title = "Notification"
    return title, body


class NotificationLogsService:
    """Service for listing notification logs visible to the current user."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = NotificationLogsRepository(session)

    async def list_my_notifications(self, user_id: UUID) -> MyNotificationsResponse:
        """
        Return the latest notification log rows for ``user_id`` (max :const:`_MY_NOTIFICATIONS_MAX`).
        """
        rows = await self.repository.list_for_user(user_id, limit=_MY_NOTIFICATIONS_MAX, offset=0)
        items: list[MyNotificationItem] = []
        for row in rows:
            payload = _parse_payload_snapshot(getattr(row, "payload_snapshot", None))
            title, body = _title_body_from_payload(payload)
            items.append(
                MyNotificationItem(
                    id=row.id,
                    title=title,
                    body=body,
                    send_status=row.send_status,
                    channel=row.channel,
                    created_at=row.created_at,
                    sent_at=row.sent_at,
                )
            )
        return MyNotificationsResponse(items=items)
