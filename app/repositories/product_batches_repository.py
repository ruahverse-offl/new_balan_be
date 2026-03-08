"""
Product Batches Repository
Data access layer for product_batches
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import ProductBatch


class ProductBatchesRepository(BaseRepository[ProductBatch]):
    """Repository for product_batches table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ProductBatch, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for product_batches."""
        return ["batch_number"]
