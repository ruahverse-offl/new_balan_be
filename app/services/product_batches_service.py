"""
Product Batches Service
Business logic layer for product_batches
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from sqlalchemy import select
from app.db.models import InventoryTransaction, OrderItem, Order
from app.repositories.product_batches_repository import ProductBatchesRepository
from app.schemas.product_batches_schema import (
    ProductBatchCreateRequest,
    ProductBatchUpdateRequest,
    ProductBatchResponse,
    ProductBatchListResponse,
    ProductBatchDetailResponse,
    BatchDetailTransactionSummary,
    BatchDetailOrderItemSummary,
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class ProductBatchesService(BaseService):
    """Service for product_batches operations."""
    
    def __init__(self, session: AsyncSession):
        repository = ProductBatchesRepository(session)
        super().__init__(repository, session)
    
    async def create_product_batch(
        self,
        data: ProductBatchCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> ProductBatchResponse:
        """Create a new product batch."""
        logger.info(f"Creating product batch: {data.batch_number}")
        batch_data = data.model_dump()
        batch = await self.repository.create(batch_data, created_by, created_ip)
        batch_dict = self._model_to_dict(batch)
        return ProductBatchResponse(**batch_dict)
    
    async def get_product_batch_by_id(self, batch_id: UUID) -> Optional[ProductBatchResponse]:
        """Get product batch by ID."""
        batch = await self.repository.get_by_id(batch_id)
        if not batch:
            return None
        batch_dict = self._model_to_dict(batch)
        return ProductBatchResponse(**batch_dict)

    async def get_batch_detail(self, batch_id: UUID) -> Optional[ProductBatchDetailResponse]:
        """Get full batch detail: batch + inventory transactions for this batch + order items that used this batch."""
        batch = await self.repository.get_by_id(batch_id)
        if not batch:
            return None
        batch_response = ProductBatchResponse(**self._model_to_dict(batch))

        # Transactions for this batch
        txn_stmt = (
            select(InventoryTransaction)
            .where(
                InventoryTransaction.product_batch_id == batch_id,
                InventoryTransaction.is_deleted == False,
            )
            .order_by(InventoryTransaction.created_at.desc())
        )
        txn_result = await self.session.execute(txn_stmt)
        txns = txn_result.scalars().all()
        transactions = [
            BatchDetailTransactionSummary(
                id=t.id,
                transaction_type=t.transaction_type or "",
                quantity_change=t.quantity_change or 0,
                reference_order_id=t.reference_order_id,
                remarks=t.remarks,
                created_at=t.created_at,
            )
            for t in txns
        ]

        # Order items that used this batch (join Order for order_reference)
        items_stmt = (
            select(OrderItem, Order.order_reference)
            .join(Order, OrderItem.order_id == Order.id)
            .where(
                OrderItem.product_batch_id == batch_id,
                OrderItem.is_deleted == False,
            )
            .order_by(OrderItem.created_at.desc())
        )
        items_result = await self.session.execute(items_stmt)
        rows = items_result.all()
        order_items = [
            BatchDetailOrderItemSummary(
                id=row[0].id,
                order_id=row[0].order_id,
                order_reference=row[1],
                medicine_name=row[0].medicine_name,
                brand_name=row[0].brand_name,
                quantity=row[0].quantity,
                unit_price=row[0].unit_price,
                total_price=row[0].total_price,
                created_at=row[0].created_at,
            )
            for row in rows
        ]

        return ProductBatchDetailResponse(
            batch=batch_response,
            transactions=transactions,
            order_items=order_items,
        )

    async def get_product_batches_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> ProductBatchListResponse:
        """Get list of product batches with pagination, search, and sort."""
        batches, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        batch_responses = [
            ProductBatchResponse(**self._model_to_dict(b)) for b in batches
        ]
        return ProductBatchListResponse(
            items=batch_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_product_batch(
        self,
        batch_id: UUID,
        data: ProductBatchUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[ProductBatchResponse]:
        """Update a product batch."""
        logger.info(f"Updating product batch: {batch_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        batch = await self.repository.update(batch_id, update_data, updated_by, updated_ip)
        if not batch:
            return None
        batch_dict = self._model_to_dict(batch)
        return ProductBatchResponse(**batch_dict)
    
    async def delete_product_batch(
        self,
        batch_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a product batch."""
        logger.info(f"Deleting product batch: {batch_id}")
        return await self.repository.soft_delete(batch_id, updated_by, updated_ip)
