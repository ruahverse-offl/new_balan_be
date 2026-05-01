"""
Send a one-off Expo test push to every push-enabled token for a user (admin tooling).

Writes ``T_notification_logs`` rows tied to notification master ``TEST_NOTIFICATION``.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.repositories.notification_logs_repository import NotificationLogsRepository
from app.repositories.notification_master_repository import NotificationMasterRepository
from app.repositories.notification_settings_repository import NotificationSettingsRepository
from app.services.delivery_assignment_push_service import _parse_expo_data_statuses

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
    Build Expo messages for ``target_user_id`` and POST to Expo push API.

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
        Send Expo push(es) for ``target_user_id``.

        Returns:
            Tuple of (number of messages POSTed to Expo, list of dicts per token:
            ``expo_push_token``, ``status``, ``detail``).
        """
        master = await self._ensure_master(audit_user_id, audit_ip)
        settings_rows = await self._settings_repo.list_push_enabled_for_user(target_user_id)
        if not settings_rows:
            return (
                0,
                [{"expo_push_token": "", "status": "skipped", "detail": "No push-enabled Expo tokens"}],
            )

        payload_for_inbox = json.dumps({"title": title, "body": body, "event": _EVENT_CODE}, default=str)
        data_payload = {"event": _EVENT_CODE, "kind": "test"}

        messages: List[Dict[str, Any]] = []
        setting_id_per_message: List[Optional[UUID]] = []
        for s in settings_rows:
            token = (s.expo_push_token or "").strip()
            if not token:
                continue
            msg: Dict[str, Any] = {
                "to": token,
                "title": title,
                "body": body,
                "data": data_payload,
                "sound": "default",
                "priority": "high",
            }
            ch = (android_channel_id or "").strip()
            if ch:
                msg["channelId"] = ch
            elif (s.device_platform or "").strip().lower() == "android":
                # Prefer customer-app default channel unless caller overrides globally.
                msg["channelId"] = "default"
            messages.append(msg)
            setting_id_per_message.append(s.id)

        if not messages:
            return (
                0,
                [{"expo_push_token": "", "status": "skipped", "detail": "Tokens present but empty after trim"}],
            )

        settings = get_settings()
        raw_url = (getattr(settings, "EXPO_PUSH_API_URL", None) or "").strip()
        url = raw_url or "https://exp.host/--/api/v2/push/send"
        headers: Dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        auth_tok = (getattr(settings, "EXPO_ACCESS_TOKEN", None) or "").strip()
        if auth_tok:
            headers["Authorization"] = f"Bearer {auth_tok}"

        request_body: Any = messages[0] if len(messages) == 1 else messages

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(str(url), json=request_body, headers=headers)

        try:
            response_json = resp.json()
        except Exception:
            response_json = {"raw": resp.text[:2000]}

        if resp.status_code < 200 or resp.status_code >= 300:
            response_json = {
                "data": [
                    {
                        "status": "error",
                        "message": f"HTTP {resp.status_code}: {str(response_json)[:500]}",
                    }
                ]
            }

        parsed = _parse_expo_data_statuses(response_json, len(messages))
        now_utc = datetime.now(timezone.utc)
        out: List[Dict[str, Any]] = []

        for idx, msg in enumerate(messages):
            token_used = str(msg.get("to") or "")
            setting_id: Optional[UUID] = (
                setting_id_per_message[idx] if idx < len(setting_id_per_message) else None
            )
            ticket = parsed[idx] if idx < len(parsed) else {"status": "error", "message": "no_ticket"}
            ok = str(ticket.get("status", "")).lower() == "ok"
            err_text: Optional[str] = None
            if not ok:
                err_text = str(ticket.get("message") or ticket.get("error") or resp.reason_phrase)

            await self._logs_repo.create(
                {
                    "user_id": target_user_id,
                    "notification_master_id": master.id,
                    "notification_setting_id": setting_id,
                    "channel": "push",
                    "expo_push_token": token_used or None,
                    "payload_snapshot": payload_for_inbox,
                    "send_status": "sent" if ok else "failed",
                    "provider_response": json.dumps(ticket, default=str)[:8000],
                    "error_message": err_text[:2000] if err_text else None,
                    "retry_count": 0,
                    "sent_at": now_utc if ok else None,
                },
                audit_user_id,
                audit_ip,
            )
            out.append(
                {
                    "expo_push_token": token_used,
                    "status": "ok" if ok else "error",
                    "detail": None if ok else (err_text or "unknown_error"),
                }
            )

        await self.session.flush()
        logger.info(
            "Test push for user_id=%s: %s message(s), http=%s",
            target_user_id,
            len(messages),
            resp.status_code,
        )
        return len(messages), out
