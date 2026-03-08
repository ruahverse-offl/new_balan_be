"""
Doctors Repository
Data access layer for doctors
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Doctor


class DoctorsRepository(BaseRepository[Doctor]):
    """Repository for doctors table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Doctor, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for doctors."""
        return ["name", "specialty", "qualifications"]
