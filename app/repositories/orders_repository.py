"""
Orders Repository
Data access layer for orders
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Order


class OrdersRepository(BaseRepository[Order]):
    """Repository for orders table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Order, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for orders."""
        return ["order_source", "order_status", "approval_status"]
