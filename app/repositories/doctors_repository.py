"""
Doctors Repository
Data access layer for doctors
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Doctor


class DoctorsRepository(BaseRepository[Doctor]):
    """Repository for doctors table."""

    def __init__(self, session: AsyncSession):
        super().__init__(Doctor, session)

    # Search uses BaseRepository._get_searchable_fields(): all String/Text columns on Doctor.
