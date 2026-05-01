"""
Send Expo push notifications when an order is assigned (or reassigned) to a delivery agent.

Uses ``M_notification_master`` (event ``DELIVERY_ASSIGNED``), ``M_notification_settings`` tokens,
and logs each attempt in ``T_notification_logs``. Failures do not roll back the order update.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import NotificationMaster, Order
from app.repositories.notification_logs_repository import NotificationLogsRepository
from app.repositories.notification_master_repository import NotificationMasterRepository
from app.repositories.notification_settings_repository import NotificationSettingsRepository

logger = logging.getLogger(__name__)

_EVENT_CODE = "DELIVERY_ASSIGNED"
_DEFAULT_CHANNEL_TEMPLATES = {
    "push": {
        "title_template": "New delivery assigned",
        "body_template": "Order {{order_reference}} for {{customer_name}}. Open the app to view.",
        "message_variables": ["order_reference", "customer_name", "order_status", "delivery_address"],
        "is_enabled": True,
    }
}


def _render_template(template: str, values: Dict[str, str]) -> str:
    """Replace ``{{name}}`` placeholders with string values (missing keys become empty)."""

    def _sub(m: re.Match[str]) -> str:
        return str(values.get(m.group(1).strip(), ""))

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", _sub, template or "")


def _order_context(order: Order) -> Dict[str, str]:
    ref = getattr(order, "order_reference", None) or ""
    if not (ref and str(ref).strip()):
        ref = str(order.id)
    return {
        "order_reference": str(ref)[:120],
        "customer_name": (str(getattr(order, "customer_name", None) or "Customer"))[:120],
        "order_status": str(getattr(order, "order_status", "") or "")[:80],
        "delivery_address": (str(getattr(order, "delivery_address", None) or ""))[:300],
    }


def _parse_expo_data_statuses(response_json: Any, num_messages: int) -> List[Dict[str, Any]]:
    """
    Normalize Expo push API JSON into one dict per sent message (success / error).

    Handles single-message and batch responses.
    """
    if not isinstance(response_json, dict):
        return [{"status": "error", "message": "invalid_expo_response"} for _ in range(num_messages)]

    data = response_json.get("data")
    if data is None:
        err = response_json.get("errors")
        msg = "expo_error"
        if isinstance(err, list) and err:
            msg = str(err[0])
        return [{"status": "error", "message": msg} for _ in range(num_messages)]

    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        out: List[Dict[str, Any]] = []
        for i in range(num_messages):
            if i < len(data) and isinstance(data[i], dict):
                out.append(data[i])
            else:
                out.append({"status": "error", "message": "missing_ticket"})
        return out
    return [{"status": "error", "message": "unexpected_data_shape"} for _ in range(num_messages)]


class DeliveryAssignmentPushService:
    """
    Notify a delivery agent via Expo push when they receive an order assignment.

    Inputs: SQLAlchemy session, order row after persist, target agent user id, audit fields for logs.
    Output: none; logs and HTTP errors are swallowed so order updates always succeed.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._master_repo = NotificationMasterRepository(session)
        self._settings_repo = NotificationSettingsRepository(session)
        self._logs_repo = NotificationLogsRepository(session)

    async def _ensure_master(self, audit_user_id: UUID, audit_ip: str) -> Optional[NotificationMaster]:
        existing = await self._master_repo.get_active_by_event_code(_EVENT_CODE)
        if existing:
            return existing
        try:
            row = await self._master_repo.create(
                {
                    "event_code": _EVENT_CODE,
                    "event_name": "Delivery assigned",
                    "description": "Fired when staff assigns or reassigns a delivery agent",
                    "channel_templates": json.dumps(_DEFAULT_CHANNEL_TEMPLATES),
                    "is_active": True,
                },
                audit_user_id,
                audit_ip,
            )
            await self.session.flush()
            return row
        except Exception:
            logger.exception(
                "Could not create notification master for %s; push skipped", _EVENT_CODE
            )
            return None

    async def notify_agent_assigned(
        self,
        *,
        agent_user_id: UUID,
        order: Order,
        audit_user_id: UUID,
        audit_ip: str,
    ) -> None:
        """
        Load templates and device tokens, send Expo push(es), write ``T_notification_logs``.

        Accepts:
            agent_user_id — delivery agent ``M_users.id``
            order — persisted order row (assignment already saved)
            audit_user_id / audit_ip — staff actor for log / master seed rows

        Returns:
            None. Never raises to callers.
        """
        try:
            master = await self._ensure_master(audit_user_id, audit_ip)
            if not master:
                return

            try:
                channels = json.loads(master.channel_templates or "{}")
            except json.JSONDecodeError:
                channels = {}
            push_cfg = channels.get("push") if isinstance(channels, dict) else {}
            if isinstance(push_cfg, dict) and push_cfg.get("is_enabled") is False:
                logger.info("Push disabled in master for %s; skipping", _EVENT_CODE)
                return

            ctx = _order_context(order)
            title_t = (push_cfg or {}).get("title_template") or _DEFAULT_CHANNEL_TEMPLATES["push"][
                "title_template"
            ]
            body_t = (push_cfg or {}).get("body_template") or _DEFAULT_CHANNEL_TEMPLATES["push"][
                "body_template"
            ]
            title = _render_template(str(title_t), ctx)
            body = _render_template(str(body_t), ctx)

            payload_for_inbox = json.dumps(
                {"title": title, "body": body, "orderId": str(order.id), "event": _EVENT_CODE},
                default=str,
            )

            data_payload = {
                "orderId": str(order.id),
                "event": _EVENT_CODE,
            }

            settings_rows = await self._settings_repo.list_push_enabled_for_user(agent_user_id)
            if not settings_rows:
                logger.info(
                    "No push-enabled Expo tokens for delivery agent user_id=%s; assignment push skipped",
                    agent_user_id,
                )
                return

            messages: List[Dict[str, Any]] = []
            setting_id_per_message: List[Optional[UUID]] = []
            for s in settings_rows:
                token = (s.expo_push_token or "").strip()
                if not token:
                    continue
                messages.append(
                    {
                        "to": token,
                        "title": title,
                        "body": body,
                        "data": data_payload,
                        "sound": "default",
                        "priority": "high",
                        "channelId": "delivery_default",
                    }
                )
                setting_id_per_message.append(s.id)

            if not messages:
                return

            settings = get_settings()
            raw_url = (getattr(settings, "EXPO_PUSH_API_URL", None) or "").strip()
            url = raw_url or "https://exp.host/--/api/v2/push/send"
            headers: Dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
            token = (getattr(settings, "EXPO_ACCESS_TOKEN", None) or "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"

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
                        {"status": "error", "message": f"HTTP {resp.status_code}: {str(response_json)[:500]}"}
                    ]
                }

            parsed = _parse_expo_data_statuses(response_json, len(messages))
            now_utc = datetime.now(timezone.utc)

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
                        "user_id": agent_user_id,
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
            await self.session.flush()

        except Exception:
            logger.exception(
                "Delivery assignment push failed (order_id=%s agent=%s)",
                getattr(order, "id", None),
                agent_user_id,
            )
