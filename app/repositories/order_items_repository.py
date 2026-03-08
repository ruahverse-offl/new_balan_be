"""
Order Items Repository
Data access layer for order_items
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import OrderItem


class OrderItemsRepository(BaseRepository[OrderItem]):
    """Repository for order_items table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(OrderItem, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for order items."""
        return []
