"""
Orders Service
Business logic layer for orders
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sa_update
import logging

from fastapi import HTTPException, status

from app.repositories.orders_repository import OrdersRepository
from app.db.models import OrderItem, Payment, User, IST
from app.config import get_settings
from app.utils.datetime_utils import get_current_ist_time
from app.domain import order_lifecycle as lc
from app.schemas.orders_schema import (
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderResponse,
    OrderListResponse,
    OrderDetailResponse,
    OrderSalesSummaryResponse,
)
from app.schemas.order_items_schema import OrderItemResponse
from app.schemas.payments_schema import PaymentResponse
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.services.delivery_assignment_push_service import DeliveryAssignmentPushService

logger = logging.getLogger(__name__)
settings = get_settings()

# Fields a delivery agent may PATCH on orders assigned to them (no staff role).
_DELIVERY_PATCH_KEYS: Set[str] = {"order_status", "return_reason"}


class OrdersService(BaseService):
    """Service for orders operations."""

    def __init__(self, session: AsyncSession):
        repository = OrdersRepository(session)
        super().__init__(repository, session)

    @staticmethod
    def _payment_grace_minutes() -> int:
        try:
            raw = int(getattr(settings, "PAYMENT_GRACE_MINUTES", 30))
        except Exception:
            raw = 30
        return max(1, raw)

    def _payment_due_at(self, created_at: Optional[datetime]) -> datetime:
        base = created_at or datetime.now(timezone.utc)
        if base.tzinfo is None:
            # Treat naive DB values as IST wall-clock, then normalize to UTC.
            base = base.replace(tzinfo=IST).astimezone(timezone.utc)
        else:
            base = base.astimezone(timezone.utc)
        return base + timedelta(minutes=self._payment_grace_minutes())

    def _seconds_until_due(self, created_at: Optional[datetime]) -> int:
        rem = int((self._payment_due_at(created_at) - datetime.now(timezone.utc)).total_seconds())
        max_window = self._payment_grace_minutes() * 60
        if rem > max_window:
            # Defensive correction for legacy rows with timezone-skewed created_at values.
            rem -= 5 * 60 * 60 + 30 * 60
        rem = min(rem, max_window)
        return max(0, rem)

    async def _expire_pending_payment_if_due_for_order(self, order_id: UUID) -> bool:
        """
        Ensure stale unpaid orders are reflected as FAILED/PAYMENT_CANCELLED.
        Used by order read APIs so My Orders always shows current state.
        """
        row = (
            await self.session.execute(
                select(Payment, self.repository.model)
                .join(self.repository.model, Payment.order_id == self.repository.model.id)
                .where(
                    self.repository.model.id == order_id,
                    self.repository.model.is_deleted == False,  # noqa: E712
                    Payment.is_deleted == False,  # noqa: E712
                )
            )
        ).first()
        if not row:
            return False
        payment, order = row
        if payment.payment_status == "SUCCESS":
            return False
        if lc.normalize_order_status(order.order_status) != lc.PAYMENT_PENDING:
            return False
        if self._seconds_until_due(order.created_at) > 0:
            return False

        reason = "Payment window expired without successful payment."
        actor_id = order.customer_id or payment.created_by
        await self.session.execute(
            sa_update(Payment)
            .where(Payment.id == payment.id)
            .values(
                payment_status="FAILED",
                gateway_response=json.dumps(
                    {"checkout_outcome": "expired", "error_description": reason},
                    default=str,
                ),
                updated_by=actor_id,
                updated_ip="orders-service-expiry",
            )
        )
        await self.session.execute(
            sa_update(self.repository.model)
            .where(self.repository.model.id == order.id)
            .values(
                order_status=lc.PAYMENT_CANCELLED,
                cancellation_reason=reason,
                cancelled_by_user_id=actor_id,
                cancelled_at=datetime.now(IST),
                updated_by=actor_id,
                updated_ip="orders-service-expiry",
            )
        )
        await self.session.commit()
        return True

    async def create_order(
        self,
        data: OrderCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> OrderResponse:
        """Create a new order."""
        logger.info(f"Creating order for customer: {data.customer_id}")
        order_data = data.model_dump()
        order = await self.repository.create(order_data, created_by, created_ip)
        order_dict = self._model_to_dict(order)
        return OrderResponse(**order_dict)

    async def get_order_by_id(self, order_id: UUID) -> Optional[OrderResponse]:
        """Get order by ID."""
        await self._expire_pending_payment_if_due_for_order(order_id)
        order = await self.repository.get_by_id(order_id)
        if not order:
            return None
        order_dict = self._model_to_dict(order)
        return OrderResponse(**order_dict)

    async def get_order_detail(self, order_id: UUID) -> Optional[OrderDetailResponse]:
        """Get full order detail: order, items, and payment (for transaction/refund reference)."""
        await self._expire_pending_payment_if_due_for_order(order_id)
        order = await self.repository.get_by_id(order_id)
        if not order:
            return None
        order_dict = self._model_to_dict(order)
        assigned_user_id = order_dict.get("delivery_assigned_user_id")
        if assigned_user_id:
            assigned_stmt = select(User).where(
                User.id == assigned_user_id,
                User.is_deleted == False,  # noqa: E712
            )
            assigned_row = (await self.session.execute(assigned_stmt)).scalar_one_or_none()
            if assigned_row:
                order_dict["delivery_assigned_user_name"] = assigned_row.full_name
                order_dict["delivery_assigned_user_phone"] = assigned_row.mobile_number
        order_response = OrderResponse(**order_dict)

        items_stmt = select(OrderItem).where(
            OrderItem.order_id == order_id,
            OrderItem.is_deleted == False,
        )
        items_result = await self.session.execute(items_stmt)
        items = items_result.scalars().all()
        items_responses = [OrderItemResponse(**self._model_to_dict(i)) for i in items]

        payment_stmt = select(Payment).where(
            Payment.order_id == order_id,
            Payment.is_deleted == False,
        )
        payment_result = await self.session.execute(payment_stmt)
        payment_row = payment_result.scalar_one_or_none()
        payment_response = PaymentResponse(**self._model_to_dict(payment_row)) if payment_row else None

        return OrderDetailResponse(order=order_response, items=items_responses, payment=payment_response)

    async def get_orders_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        user_id: Optional[UUID] = None,
        delivery_assigned_user_id: Optional[UUID] = None,
        delivery_agent_status_scope: Optional[str] = None,
        staff_scope: Optional[str] = None,
        order_status: Optional[str] = None,
        order_date: Optional[str] = None,
    ) -> OrderListResponse:
        """Get list of orders with pagination, search, and sort."""
        additional_filters: Dict[str, Any] = {}
        if user_id:
            additional_filters["customer_id"] = user_id
        if delivery_assigned_user_id:
            additional_filters["delivery_assigned_user_id"] = delivery_assigned_user_id
        if order_status:
            additional_filters["order_status"] = order_status
        list_kw: Dict[str, Any] = dict(
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            additional_filters=additional_filters if additional_filters else None,
        )
        if delivery_agent_status_scope:
            list_kw["delivery_agent_status_scope"] = delivery_agent_status_scope
        if staff_scope:
            list_kw["staff_scope"] = staff_scope
        if order_date:
            list_kw["order_date"] = order_date
        orders, pagination = await self.repository.get_list(**list_kw)
        # Keep list view consistent with payment grace window behavior.
        for o in orders:
            await self._expire_pending_payment_if_due_for_order(o.id)
        if orders:
            orders, pagination = await self.repository.get_list(**list_kw)
        order_responses = [
            OrderResponse(**self._model_to_dict(o)) for o in orders
        ]
        return OrderListResponse(
            items=order_responses,
            pagination=PaginationResponse(**pagination)
        )

    async def update_order(
        self,
        order_id: UUID,
        data: OrderUpdateRequest,
        updated_by: UUID,
        updated_ip: str,
        *,
        can_order_update: bool,
        can_delivery_update: bool,
    ) -> Optional[OrderResponse]:
        """Update an order with lifecycle rules for status changes."""
        logger.info(f"Updating order: {order_id}")
        patch: Dict[str, Any] = dict(data.model_dump(exclude_unset=True))

        order = await self.repository.get_by_id(order_id)
        if not order:
            return None

        actor_is_staff = can_order_update
        assigned_id = order.delivery_assigned_user_id
        actor_is_assigned_delivery = bool(
            can_delivery_update and assigned_id is not None and assigned_id == updated_by
        )

        if not can_order_update and not can_delivery_update:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: ORDER_UPDATE or DELIVERY_ORDER_UPDATE required.",
            )

        if can_delivery_update and not can_order_update:
            extra = set(patch.keys()) - _DELIVERY_PATCH_KEYS
            if extra:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Delivery role may only update: {sorted(_DELIVERY_PATCH_KEYS)}.",
                )
            if assigned_id != updated_by:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update orders assigned to you.",
                )

        new_status = patch.get("order_status")
        if new_status is not None:
            new_status = str(new_status).strip().upper()
            patch["order_status"] = new_status

        if new_status is not None:
            chk = lc.validate_status_transition(
                order.order_status,
                new_status,
                actor_is_staff=actor_is_staff,
                actor_is_assigned_delivery=actor_is_assigned_delivery,
            )
            if not chk.ok:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=chk.error)

            if new_status == lc.DELIVERY_ASSIGNED:
                assign_id = patch.get("delivery_assigned_user_id", order.delivery_assigned_user_id)
                if assign_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="delivery_assigned_user_id is required when setting DELIVERY_ASSIGNED.",
                    )

            if new_status == lc.CANCELLED_BY_STAFF:
                reason = (patch.get("cancellation_reason") or "").strip()
                if not reason:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="cancellation_reason is required for CANCELLED_BY_STAFF.",
                    )
                patch["cancelled_by_user_id"] = updated_by
                patch["cancelled_at"] = datetime.now(IST)

            if new_status == lc.DELIVERY_RETURNED:
                if not (patch.get("return_reason") or "").strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="return_reason is required for DELIVERY_RETURNED.",
                    )

            if lc.delivery_agent_must_be_assigned_for_transition(order.order_status, new_status):
                if order.delivery_assigned_user_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Assign a delivery user before this status.",
                    )
                if not actor_is_staff and order.delivery_assigned_user_id != updated_by:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only the assigned delivery user can perform this delivery step.",
                    )

            now_ts = get_current_ist_time()
            if new_status == lc.ORDER_RECEIVED and not getattr(order, "order_received_at", None):
                patch["order_received_at"] = now_ts
            if new_status in (lc.ORDER_TAKEN, lc.ORDER_PROCESSING) and not getattr(order, "order_packed_at", None):
                patch["order_packed_at"] = now_ts
            if new_status == lc.DELIVERY_ASSIGNED:
                patch["delivery_assigned_at"] = now_ts
            if new_status == lc.DELIVERED:
                patch["delivered_at"] = now_ts

        elif "delivery_assigned_user_id" in patch:
            if not actor_is_staff:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only staff can change delivery_assigned_user_id.",
                )
            cur = lc.normalize_order_status(order.order_status)
            if cur != lc.DELIVERY_ASSIGNED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only reassign delivery when order_status is DELIVERY_ASSIGNED.",
                )
            patch["delivery_assigned_at"] = get_current_ist_time()

        # Resolve push targets — only set for events the delivery agent must know about.
        notify_assigned_agent_id: Optional[UUID] = None   # fires DELIVERY_ASSIGNED push
        notify_cancelled_agent_id: Optional[UUID] = None  # fires ORDER_CANCELLED_DELIVERY push
        if new_status == lc.DELIVERY_ASSIGNED:
            notify_assigned_agent_id = patch.get("delivery_assigned_user_id") or order.delivery_assigned_user_id
        elif "delivery_assigned_user_id" in patch:
            notify_assigned_agent_id = patch.get("delivery_assigned_user_id")
        elif new_status == lc.CANCELLED_BY_STAFF:
            notify_cancelled_agent_id = getattr(order, "delivery_assigned_user_id", None)

        order = await self.repository.update(order_id, patch, updated_by, updated_ip)
        if not order:
            return None

        push_svc = DeliveryAssignmentPushService(self.session)
        if notify_assigned_agent_id is not None:
            await push_svc.notify_agent_assigned(
                agent_user_id=notify_assigned_agent_id,
                order=order,
                audit_user_id=updated_by,
                audit_ip=updated_ip,
            )
        if notify_cancelled_agent_id is not None:
            await push_svc.notify_order_cancelled(
                agent_user_id=notify_cancelled_agent_id,
                order=order,
                audit_user_id=updated_by,
                audit_ip=updated_ip,
            )

        order_dict = self._model_to_dict(order)
        return OrderResponse(**order_dict)

    async def get_sales_summary(self) -> OrderSalesSummaryResponse:
        """Aggregated sales figures for the admin KPI strip."""
        data = await self.repository.get_sales_summary()
        return OrderSalesSummaryResponse(**data)

    async def delete_order(
        self,
        order_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete an order."""
        logger.info(f"Deleting order: {order_id}")
        return await self.repository.soft_delete(order_id, updated_by, updated_ip)
