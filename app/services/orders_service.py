"""
Orders Service
Business logic layer for orders
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.repositories.orders_repository import OrdersRepository
from app.repositories.inventory_transactions_repository import InventoryTransactionsRepository
from app.db.models import OrderItem, ProductBatch, Payment
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
        user_id: Optional[UUID] = None
    ) -> OrderListResponse:
        """Get list of orders with pagination, search, and sort."""
        additional_filters = {}
        if user_id:
            additional_filters["customer_id"] = user_id
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
        updated_ip: str
    ) -> Optional[OrderResponse]:
        """Update an order."""
        logger.info(f"Updating order: {order_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        order = await self.repository.update(order_id, update_data, updated_by, updated_ip)
        if not order:
            return None

        # When order is approved, create inventory SALE transactions to decrement stock
        if "approval_status" in update_data and update_data["approval_status"].upper() == "APPROVED":
            await self._create_sale_transactions(order_id, updated_by, updated_ip)

        order_dict = self._model_to_dict(order)
        return OrderResponse(**order_dict)
    
    async def _create_sale_transactions(
        self,
        order_id: UUID,
        created_by: UUID,
        created_ip: str
    ):
        """Create inventory SALE transactions for each order item and decrement batch stock."""
        try:
            # Fetch order items
            stmt = select(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.is_deleted == False
            )
            result = await self.session.execute(stmt)
            items = result.scalars().all()

            inv_repo = InventoryTransactionsRepository(self.session)

            for item in items:
                # Find the latest batch for this medicine brand with available stock
                batch_stmt = (
                    select(ProductBatch)
                    .where(ProductBatch.medicine_brand_id == item.medicine_brand_id)
                    .where(ProductBatch.is_deleted == False)
                    .where(ProductBatch.quantity_available >= item.quantity)
                    .order_by(ProductBatch.expiry_date.asc())  # FEFO: first expiry, first out
                    .limit(1)
                )
                batch_result = await self.session.execute(batch_stmt)
                batch = batch_result.scalar_one_or_none()

                if batch:
                    # Decrement batch stock
                    batch.quantity_available -= item.quantity

                    # Record which batch was used on the order item (for audit/recalls)
                    item.product_batch_id = batch.id

                    # Create inventory transaction record
                    txn_data = {
                        "medicine_brand_id": item.medicine_brand_id,
                        "product_batch_id": batch.id,
                        "transaction_type": "SALE",
                        "quantity_change": -item.quantity,
                        "reference_order_id": order_id,
                        "remarks": f"Order approved - sold {item.quantity} units"
                    }
                    await inv_repo.create(txn_data, created_by, created_ip)
                else:
                    logger.warning(
                        f"No batch with sufficient stock for medicine_brand_id={item.medicine_brand_id}, "
                        f"order_id={order_id}, qty={item.quantity}"
                    )

            await self.session.flush()
            logger.info(f"Inventory sale transactions created for order {order_id}")
        except Exception as e:
            logger.error(f"Error creating sale transactions for order {order_id}: {e}")

    async def delete_order(
        self,
        order_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete an order."""
        logger.info(f"Deleting order: {order_id}")
        return await self.repository.soft_delete(order_id, updated_by, updated_ip)
