"""
Medicine Brands Repository
Data access layer for medicine_brands
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import MedicineBrand


class MedicineBrandsRepository(BaseRepository[MedicineBrand]):
    """Repository for medicine_brands table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(MedicineBrand, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for medicine_brands."""
        return ["brand_name", "manufacturer", "description"]
