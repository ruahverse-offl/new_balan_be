"""
Therapeutic Categories Repository
Data access layer for therapeutic_categories
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import TherapeuticCategory


class TherapeuticCategoriesRepository(BaseRepository[TherapeuticCategory]):
    """Repository for therapeutic_categories table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TherapeuticCategory, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for therapeutic_categories."""
        return ["name", "description"]
