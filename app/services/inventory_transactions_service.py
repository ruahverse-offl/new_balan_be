"""
Inventory Transactions Service
Business logic layer for inventory_transactions.
Ensures product_batch belongs to medicine_brand and updates batch quantity when creating transactions.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from fastapi import HTTPException, status

from app.repositories.inventory_transactions_repository import InventoryTransactionsRepository
from app.schemas.inventory_transactions_schema import (
    InventoryTransactionCreateRequest,
    InventoryTransactionUpdateRequest,
    InventoryTransactionResponse,
    InventoryTransactionListResponse,
    InventoryTransactionDetailResponse,
    OrderSummaryForTransaction,
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.db.models import ProductBatch, Order

logger = logging.getLogger(__name__)


class InventoryTransactionsService(BaseService):
    """Service for inventory_transactions operations."""
    
    def __init__(self, session: AsyncSession):
        repository = InventoryTransactionsRepository(session)
        super().__init__(repository, session)
    
    async def create_inventory_transaction(
        self,
        data: InventoryTransactionCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> InventoryTransactionResponse:
        """Create a new inventory transaction. Validates batch belongs to brand and updates batch quantity."""
        logger.info(f"Creating inventory transaction: {data.transaction_type}")
        # Ensure product_batch exists and belongs to the given medicine_brand (correct relation)
        batch_stmt = select(ProductBatch).where(
            ProductBatch.id == data.product_batch_id,
            ProductBatch.is_deleted == False,
        )
        result = await self.session.execute(batch_stmt)
        batch = result.scalar_one_or_none()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product batch not found",
            )
        if str(batch.medicine_brand_id) != str(data.medicine_brand_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product batch does not belong to the selected medicine brand",
            )
        # For outbound (negative quantity), ensure batch has enough stock
        if data.quantity_change < 0 and (batch.quantity_available or 0) < abs(data.quantity_change):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Batch has {batch.quantity_available} units.",
            )
        transaction_data = data.model_dump()
        transaction = await self.repository.create(transaction_data, created_by, created_ip)
        await self.session.flush()
        # Update product batch quantity: positive = in (PURCHASE/adjustment in), negative = out (SALE/adjustment out)
        batch.quantity_available = (batch.quantity_available or 0) + data.quantity_change
        if batch.quantity_available < 0:
            batch.quantity_available = 0
        await self.session.flush()
        transaction_dict = self._model_to_dict(transaction)
        return InventoryTransactionResponse(**transaction_dict)
    
    async def get_inventory_transaction_by_id(self, transaction_id: UUID) -> Optional[InventoryTransactionResponse]:
        """Get inventory transaction by ID."""
        transaction = await self.repository.get_by_id(transaction_id)
        if not transaction:
            return None
        transaction_dict = self._model_to_dict(transaction)
        return InventoryTransactionResponse(**transaction_dict)

    async def get_inventory_transaction_detail(
        self, transaction_id: UUID
    ) -> Optional[InventoryTransactionDetailResponse]:
        """Get transaction detail with linked order summary when reference_order_id is set."""
        transaction = await self.repository.get_by_id(transaction_id)
        if not transaction:
            return None
        transaction_response = InventoryTransactionResponse(**self._model_to_dict(transaction))
        order_summary = None
        if transaction.reference_order_id:
            order_stmt = select(Order).where(
                Order.id == transaction.reference_order_id,
                Order.is_deleted == False,
            )
            order_result = await self.session.execute(order_stmt)
            order = order_result.scalar_one_or_none()
            if order:
                order_summary = OrderSummaryForTransaction(
                    order_id=order.id,
                    order_reference=order.order_reference,
                    customer_name=order.customer_name,
                    order_status=order.order_status,
                    final_amount=float(order.final_amount) if order.final_amount is not None else None,
                    created_at=order.created_at,
                )
        return InventoryTransactionDetailResponse(
            transaction=transaction_response,
            order_summary=order_summary,
        )

    async def get_inventory_transactions_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        medicine_brand_id: Optional[UUID] = None,
    ) -> InventoryTransactionListResponse:
        """Get list of inventory transactions; optionally filter by medicine_brand_id (full history for that brand)."""
        additional_filters = {"medicine_brand_id": medicine_brand_id} if medicine_brand_id else None
        transactions, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional_filters,
        )
        transaction_responses = [
            InventoryTransactionResponse(**self._model_to_dict(t)) for t in transactions
        ]
        return InventoryTransactionListResponse(
            items=transaction_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_inventory_transaction(
        self,
        transaction_id: UUID,
        data: InventoryTransactionUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[InventoryTransactionResponse]:
        """Update an inventory transaction."""
        logger.info(f"Updating inventory transaction: {transaction_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        transaction = await self.repository.update(transaction_id, update_data, updated_by, updated_ip)
        if not transaction:
            return None
        transaction_dict = self._model_to_dict(transaction)
        return InventoryTransactionResponse(**transaction_dict)
    
    async def delete_inventory_transaction(
        self,
        transaction_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete an inventory transaction."""
        logger.info(f"Deleting inventory transaction: {transaction_id}")
        return await self.repository.soft_delete(transaction_id, updated_by, updated_ip)
