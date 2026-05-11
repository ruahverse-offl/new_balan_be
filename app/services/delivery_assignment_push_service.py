"""
Send push when an order is assigned (or reassigned) to a delivery agent via FCM HTTP v1.

Uses ``M_notification_master`` (event ``DELIVERY_ASSIGNED``), ``M_notification_settings`` tokens,
and logs each attempt in ``T_notification_logs``. Failures do not roll back the order update.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order
from app.repositories.notification_logs_repository import NotificationLogsRepository
from app.repositories.notification_master_repository import NotificationMasterRepository
from app.repositories.notification_settings_repository import NotificationSettingsRepository
from app.services.fcm_push_client import send_fcm_notification

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

_CANCEL_EVENT_CODE = "ORDER_CANCELLED_DELIVERY"
_CANCEL_DEFAULT_CHANNEL_TEMPLATES = {
    "push": {
        "title_template": "Order cancelled",
        "body_template": "Order {{order_reference}} for {{customer_name}} has been cancelled by staff.",
        "message_variables": ["order_reference", "customer_name"],
        "is_enabled": True,
    }
}

_CANCEL_CUSTOMER_EVENT_CODE = "ORDER_CANCELLED_CUSTOMER"
_CANCEL_CUSTOMER_DEFAULT_CHANNEL_TEMPLATES = {
    "push": {
        "title_template": "Your order has been cancelled",
        "body_template": "Order {{order_reference}} has been cancelled by our team. A refund will be initiated if applicable.",
        "message_variables": ["order_reference"],
        "is_enabled": True,
    }
}

_SELF_CANCEL_CUSTOMER_EVENT_CODE = "ORDER_SELF_CANCELLED"
_SELF_CANCEL_CUSTOMER_DEFAULT_CHANNEL_TEMPLATES = {
    "push": {
        "title_template": "Order cancelled",
        "body_template": "Your order {{order_reference}} has been cancelled. A refund will be processed to your original payment method.",
        "message_variables": ["order_reference"],
        "is_enabled": True,
    }
}

_DELIVERY_RETURNED_EVENT_CODE = "ORDER_DELIVERY_RETURNED"
_DELIVERY_RETURNED_DEFAULT_CHANNEL_TEMPLATES = {
    "push": {
        "title_template": "Delivery update",
        "body_template": "Order {{order_reference}} could not be delivered and has been returned to our store. Our team will contact you to reschedule or process a refund.",
        "message_variables": ["order_reference"],
        "is_enabled": True,
    }
}

_REFUND_DONE_EVENT_CODE = "ORDER_REFUND_COMPLETED"
_REFUND_DONE_DEFAULT_CHANNEL_TEMPLATES = {
    "push": {
        "title_template": "Refund processed",
        "body_template": "Your refund for order {{order_reference}} has been processed. Amount will reflect in 5-7 business days.",
        "message_variables": ["order_reference"],
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


class DeliveryAssignmentPushService:
    """
    Notify a delivery agent via FCM when they receive an order assignment.

    Inputs: SQLAlchemy session, order row after persist, target agent user id, audit fields for logs.
    Output: none; logs and HTTP errors are swallowed so order updates always succeed.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._master_repo = NotificationMasterRepository(session)
        self._settings_repo = NotificationSettingsRepository(session)
        self._logs_repo = NotificationLogsRepository(session)

    async def _send_push_to_agent(
        self,
        *,
        event_code: str,
        default_templates: Dict[str, Any],
        agent_user_id: UUID,
        order: Order,
        audit_user_id: UUID,
        audit_ip: str,
    ) -> None:
        """Shared FCM push logic — load template, send to all agent devices, log each attempt."""
        try:
            existing = await self._master_repo.get_active_by_event_code(event_code)
            if existing:
                master = existing
            else:
                try:
                    master = await self._master_repo.create(
                        {
                            "event_code": event_code,
                            "event_name": default_templates.get("_event_name", event_code),
                            "description": default_templates.get("_description", ""),
                            "channel_templates": json.dumps(
                                {k: v for k, v in default_templates.items() if not k.startswith("_")}
                            ),
                            "is_active": True,
                        },
                        audit_user_id,
                        audit_ip,
                    )
                    await self.session.flush()
                except Exception:
                    logger.exception("Could not create notification master for %s; push skipped", event_code)
                    return

            if not master:
                return

            try:
                channels = json.loads(master.channel_templates or "{}")
            except json.JSONDecodeError:
                channels = {}
            push_cfg = channels.get("push") if isinstance(channels, dict) else {}
            if isinstance(push_cfg, dict) and push_cfg.get("is_enabled") is False:
                logger.info("Push disabled in master for %s; skipping", event_code)
                return

            ctx = _order_context(order)
            fallback_push = default_templates.get("push", {})
            title_t = (push_cfg or {}).get("title_template") or fallback_push.get("title_template", "")
            body_t = (push_cfg or {}).get("body_template") or fallback_push.get("body_template", "")
            title = _render_template(str(title_t), ctx)
            body = _render_template(str(body_t), ctx)

            payload_for_inbox = json.dumps(
                {"title": title, "body": body, "orderId": str(order.id), "event": event_code},
                default=str,
            )
            str_data = {"orderId": str(order.id), "event": event_code}

            settings_rows = await self._settings_repo.list_push_enabled_for_user(agent_user_id)
            if not settings_rows:
                logger.info(
                    "No push-enabled device tokens for user_id=%s; %s push skipped",
                    agent_user_id, event_code,
                )
                return

            now_utc = datetime.now(timezone.utc)

            for s in settings_rows:
                fcm_token = (s.expo_push_token or "").strip()
                if not fcm_token:
                    continue
                fcm_result = await send_fcm_notification(
                    device_token=fcm_token,
                    title=title,
                    body=body,
                    data=str_data,
                    android_channel_id="delivery_default",
                )
                ok = bool(fcm_result.get("ok"))
                err_text: Optional[str] = None if ok else str(fcm_result.get("message") or "fcm_failed")
                await self._logs_repo.create(
                    {
                        "user_id": agent_user_id,
                        "notification_master_id": master.id,
                        "notification_setting_id": s.id,
                        "channel": "push",
                        "expo_push_token": fcm_token or None,
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

            await self.session.flush()

        except Exception:
            logger.exception(
                "%s push failed (order_id=%s agent=%s)",
                event_code, getattr(order, "id", None), agent_user_id,
            )

    async def notify_agent_assigned(
        self,
        *,
        agent_user_id: UUID,
        order: Order,
        audit_user_id: UUID,
        audit_ip: str,
    ) -> None:
        """Send FCM push when an order is assigned or reassigned to a delivery agent."""
        await self._send_push_to_agent(
            event_code=_EVENT_CODE,
            default_templates={
                **_DEFAULT_CHANNEL_TEMPLATES,
                "_event_name": "Delivery assigned",
                "_description": "Fired when staff assigns or reassigns a delivery agent",
            },
            agent_user_id=agent_user_id,
            order=order,
            audit_user_id=audit_user_id,
            audit_ip=audit_ip,
        )

    async def notify_order_cancelled(
        self,
        *,
        agent_user_id: UUID,
        order: Order,
        audit_user_id: UUID,
        audit_ip: str,
    ) -> None:
        """Send FCM push to the assigned delivery agent when staff cancels an in-progress order."""
        await self._send_push_to_agent(
            event_code=_CANCEL_EVENT_CODE,
            default_templates={
                **_CANCEL_DEFAULT_CHANNEL_TEMPLATES,
                "_event_name": "Order cancelled",
                "_description": "Fired when staff cancels an order that has a delivery agent assigned",
            },
            agent_user_id=agent_user_id,
            order=order,
            audit_user_id=audit_user_id,
            audit_ip=audit_ip,
        )

    async def notify_customer_order_cancelled(
        self,
        *,
        customer_user_id: UUID,
        order: Order,
        audit_user_id: UUID,
        audit_ip: str,
    ) -> None:
        """Send FCM push to the customer when staff cancels their order."""
        await self._send_push_to_agent(
            event_code=_CANCEL_CUSTOMER_EVENT_CODE,
            default_templates={
                **_CANCEL_CUSTOMER_DEFAULT_CHANNEL_TEMPLATES,
                "_event_name": "Order cancelled by staff",
                "_description": "Fired when staff cancels a customer order",
            },
            agent_user_id=customer_user_id,
            order=order,
            audit_user_id=audit_user_id,
            audit_ip=audit_ip,
        )

    async def notify_customer_self_cancelled(
        self,
        *,
        customer_user_id: UUID,
        order: Order,
        audit_user_id: UUID,
        audit_ip: str,
    ) -> None:
        """Send FCM push confirming cancellation when customer cancels their own order."""
        await self._send_push_to_agent(
            event_code=_SELF_CANCEL_CUSTOMER_EVENT_CODE,
            default_templates={
                **_SELF_CANCEL_CUSTOMER_DEFAULT_CHANNEL_TEMPLATES,
                "_event_name": "Order self-cancelled",
                "_description": "Fired when a customer cancels their own order",
            },
            agent_user_id=customer_user_id,
            order=order,
            audit_user_id=audit_user_id,
            audit_ip=audit_ip,
        )

    async def notify_customer_delivery_returned(
        self,
        *,
        customer_user_id: UUID,
        order: Order,
        audit_user_id: UUID,
        audit_ip: str,
    ) -> None:
        """Send FCM push to the customer when delivery is returned to store."""
        await self._send_push_to_agent(
            event_code=_DELIVERY_RETURNED_EVENT_CODE,
            default_templates={
                **_DELIVERY_RETURNED_DEFAULT_CHANNEL_TEMPLATES,
                "_event_name": "Delivery returned to store",
                "_description": "Fired when delivery agent returns an order to the store",
            },
            agent_user_id=customer_user_id,
            order=order,
            audit_user_id=audit_user_id,
            audit_ip=audit_ip,
        )

    async def notify_customer_refund_completed(
        self,
        *,
        customer_user_id: UUID,
        order: Order,
        audit_user_id: UUID,
        audit_ip: str,
    ) -> None:
        """Send FCM push to the customer when their refund has been processed."""
        await self._send_push_to_agent(
            event_code=_REFUND_DONE_EVENT_CODE,
            default_templates={
                **_REFUND_DONE_DEFAULT_CHANNEL_TEMPLATES,
                "_event_name": "Refund completed",
                "_description": "Fired when a refund is successfully processed via Razorpay",
            },
            agent_user_id=customer_user_id,
            order=order,
            audit_user_id=audit_user_id,
            audit_ip=audit_ip,
        )
