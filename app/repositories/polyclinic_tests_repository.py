"""
Polyclinic Tests Repository
Data access layer for polyclinic_tests
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import PolyclinicTest


class PolyclinicTestsRepository(BaseRepository[PolyclinicTest]):
    """Repository for polyclinic_tests table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PolyclinicTest, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for polyclinic tests."""
        return ["name", "description"]
