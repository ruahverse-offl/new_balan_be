"""
Orders Service
Business logic layer for orders
"""

from datetime import datetime
from typing import Any, Dict, Optional, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from fastapi import HTTPException, status

from app.repositories.orders_repository import OrdersRepository
from app.db.models import OrderItem, Payment, IST
from app.domain import order_lifecycle as lc
from app.schemas.orders_schema import (
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderResponse,
    OrderListResponse,
    OrderDetailResponse,
)
from app.schemas.order_items_schema import OrderItemResponse
from app.schemas.payments_schema import PaymentResponse
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

# Fields a delivery agent may PATCH on orders assigned to them (no staff role).
_DELIVERY_PATCH_KEYS: Set[str] = {"order_status", "return_reason"}


class OrdersService(BaseService):
    """Service for orders operations."""

    def __init__(self, session: AsyncSession):
        repository = OrdersRepository(session)
        super().__init__(repository, session)

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
        order = await self.repository.get_by_id(order_id)
        if not order:
            return None
        order_dict = self._model_to_dict(order)
        return OrderResponse(**order_dict)

    async def get_order_detail(self, order_id: UUID) -> Optional[OrderDetailResponse]:
        """Get full order detail: order, items, and payment (for transaction/refund reference)."""
        order = await self.repository.get_by_id(order_id)
        if not order:
            return None
        order_dict = self._model_to_dict(order)
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
    ) -> OrderListResponse:
        """Get list of orders with pagination, search, and sort."""
        additional_filters: Dict[str, Any] = {}
        if user_id:
            additional_filters["customer_id"] = user_id
        if delivery_assigned_user_id:
            additional_filters["delivery_assigned_user_id"] = delivery_assigned_user_id
        orders, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional_filters if additional_filters else None
        )
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

        order = await self.repository.update(order_id, patch, updated_by, updated_ip)
        if not order:
            return None

        order_dict = self._model_to_dict(order)
        return OrderResponse(**order_dict)

    async def delete_order(
        self,
        order_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete an order."""
        logger.info(f"Deleting order: {order_id}")
        return await self.repository.soft_delete(order_id, updated_by, updated_ip)
