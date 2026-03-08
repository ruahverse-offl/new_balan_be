"""
Inventory Transactions Repository
Data access layer for inventory_transactions
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import InventoryTransaction


class InventoryTransactionsRepository(BaseRepository[InventoryTransaction]):
    """Repository for inventory_transactions table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(InventoryTransaction, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for inventory_transactions."""
        return ["transaction_type", "remarks"]
