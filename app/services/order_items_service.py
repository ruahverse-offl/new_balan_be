"""
Order Items Service
Business logic layer for order_items
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.order_items_repository import OrderItemsRepository
from app.schemas.order_items_schema import (
    OrderItemCreateRequest,
    OrderItemUpdateRequest,
    OrderItemResponse,
    OrderItemListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class OrderItemsService(BaseService):
    """Service for order_items operations."""
    
    def __init__(self, session: AsyncSession):
        repository = OrderItemsRepository(session)
        super().__init__(repository, session)
    
    async def create_order_item(
        self,
        data: OrderItemCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> OrderItemResponse:
        """Create a new order item."""
        logger.info(f"Creating order item for order: {data.order_id}")
        item_data = data.model_dump()
        item = await self.repository.create(item_data, created_by, created_ip)
        item_dict = self._model_to_dict(item)
        return OrderItemResponse(**item_dict)
    
    async def create_order_items_bulk(
        self,
        items_data: List[OrderItemCreateRequest],
        created_by: UUID,
        created_ip: str
    ) -> List[OrderItemResponse]:
        """Create multiple order items in bulk."""
        logger.info(f"Creating {len(items_data)} order items in bulk")
        items = []
        for item_data in items_data:
            data_dict = item_data.model_dump()
            item = await self.repository.create(data_dict, created_by, created_ip)
            items.append(item)
        return [OrderItemResponse(**self._model_to_dict(item)) for item in items]
    
    async def get_order_item_by_id(self, item_id: UUID) -> Optional[OrderItemResponse]:
        """Get order item by ID."""
        item = await self.repository.get_by_id(item_id)
        if not item:
            return None
        item_dict = self._model_to_dict(item)
        return OrderItemResponse(**item_dict)
    
    async def get_order_items_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        order_id: Optional[UUID] = None
    ) -> OrderItemListResponse:
        """Get list of order items with pagination, search, and sort."""
        additional_filters = {}
        if order_id:
            additional_filters["order_id"] = order_id
        
        items, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional_filters if additional_filters else None
        )
        item_responses = [
            OrderItemResponse(**self._model_to_dict(i)) for i in items
        ]
        return OrderItemListResponse(
            items=item_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_order_item(
        self,
        item_id: UUID,
        data: OrderItemUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[OrderItemResponse]:
        """Update an order item."""
        logger.info(f"Updating order item: {item_id}")
        item_data = data.model_dump(exclude_unset=True)
        item = await self.repository.update(item_id, item_data, updated_by, updated_ip)
        if not item:
            return None
        item_dict = self._model_to_dict(item)
        return OrderItemResponse(**item_dict)
    
    async def delete_order_item(
        self,
        item_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete an order item."""
        logger.info(f"Deleting order item: {item_id}")
        return await self.repository.soft_delete(item_id, updated_by, updated_ip)
