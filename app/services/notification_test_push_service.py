"""
Send a one-off FCM test push to every push-enabled token for a user (admin tooling).

Writes ``T_notification_logs`` rows tied to notification master ``TEST_NOTIFICATION``.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notification_logs_repository import NotificationLogsRepository
from app.repositories.notification_master_repository import NotificationMasterRepository
from app.repositories.notification_settings_repository import NotificationSettingsRepository
from app.services.fcm_push_client import send_fcm_notification

logger = logging.getLogger(__name__)

_EVENT_CODE = "TEST_NOTIFICATION"

_DEFAULT_PUSH_TEMPLATE = json.dumps(
    {
        "push": {
            "title_template": "Test",
            "body_template": "Test notification",
            "message_variables": [],
            "is_enabled": True,
        }
    }
)


class NotificationTestPushService:
    """
    Send FCM messages for ``target_user_id`` to all push-enabled devices.

    Requires at least one active ``M_notification_settings`` row with push enabled and a token.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._master_repo = NotificationMasterRepository(session)
        self._settings_repo = NotificationSettingsRepository(session)
        self._logs_repo = NotificationLogsRepository(session)

    async def _ensure_master(self, audit_user_id: UUID, audit_ip: str):
        existing = await self._master_repo.get_active_by_event_code(_EVENT_CODE)
        if existing:
            return existing
        row = await self._master_repo.create(
            {
                "event_code": _EVENT_CODE,
                "event_name": "Test notification",
                "description": "Manual test push sent from notification-test API",
                "channel_templates": _DEFAULT_PUSH_TEMPLATE,
                "is_active": True,
            },
            audit_user_id,
            audit_ip,
        )
        await self.session.flush()
        return row

    async def send_to_user(
        self,
        *,
        target_user_id: UUID,
        title: str,
        body: str,
        android_channel_id: Optional[str],
        audit_user_id: UUID,
        audit_ip: str,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Send FCM push(es) for ``target_user_id``.

        Returns:
            Tuple of (number of messages sent, list of dicts per token:
            ``expo_push_token``, ``status``, ``detail``).
        """
        master = await self._ensure_master(audit_user_id, audit_ip)
        settings_rows = await self._settings_repo.list_push_enabled_for_user(target_user_id)
        if not settings_rows:
            return (
                0,
                [{"expo_push_token": "", "status": "skipped", "detail": "No push-enabled tokens"}],
            )

        payload_for_inbox = json.dumps({"title": title, "body": body, "event": _EVENT_CODE}, default=str)
        data_payload = {"event": _EVENT_CODE, "kind": "test"}
        channel = (android_channel_id or "default").strip() or "default"

        now_utc = datetime.now(timezone.utc)
        out: List[Dict[str, Any]] = []
        sent_count = 0

        for s in settings_rows:
            fcm_token = (s.expo_push_token or "").strip()
            if not fcm_token:
                continue

            fcm_result = await send_fcm_notification(
                device_token=fcm_token,
                title=title,
                body=body,
                data={k: str(v) for k, v in data_payload.items()},
                android_channel_id=channel,
            )
            ok = bool(fcm_result.get("ok"))
            err_text: Optional[str] = None if ok else str(fcm_result.get("message") or "fcm_failed")

            await self._logs_repo.create(
                {
                    "user_id": target_user_id,
                    "notification_master_id": master.id,
                    "notification_setting_id": s.id,
                    "channel": "push",
                    "expo_push_token": fcm_token,
                    "payload_snapshot": payload_for_inbox,
                    "send_status": "sent" if ok else "failed",
                    "provider_response": json.dumps(fcm_result, default=str)[:8000],
                    "error_message": err_text[:2000] if err_text else None,
                    "retry_count": 0,
                    "sent_at": now_utc if ok else None,
                },
                audit_user_id,
                audit_ip,
            )
            out.append(
                {
                    "expo_push_token": fcm_token,
                    "status": "ok" if ok else "error",
                    "detail": None if ok else (err_text or "unknown_error"),
                }
            )
            sent_count += 1

        if not out:
            return (
                0,
                [{"expo_push_token": "", "status": "skipped", "detail": "Tokens present but empty after trim"}],
            )

        await self.session.flush()
        logger.info(
            "Test push for user_id=%s: %s message(s) sent via FCM",
            target_user_id,
            sent_count,
        )
        return sent_count, out
