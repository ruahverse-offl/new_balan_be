"""
Product Categories Repository
Data access layer for product_categories
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import ProductCategory


class ProductCategoriesRepository(BaseRepository[ProductCategory]):
    """Repository for product_categories table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ProductCategory, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for product categories."""
        return ["name", "description"]
