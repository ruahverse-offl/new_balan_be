"""
Medicine Compositions Repository
Data access layer for medicine_compositions
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import MedicineComposition


class MedicineCompositionsRepository(BaseRepository[MedicineComposition]):
    """Repository for medicine_compositions table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(MedicineComposition, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for medicine_compositions."""
        return ["salt_name", "strength", "unit"]
