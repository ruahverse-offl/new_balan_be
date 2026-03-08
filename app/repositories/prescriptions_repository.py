"""
Prescriptions Repository
Database operations for prescriptions
"""

from app.db.models import Prescription
from app.repositories.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class PrescriptionsRepository(BaseRepository[Prescription]):
    """Repository for prescriptions operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Prescription, session)

    def _get_searchable_fields(self):
        return ["file_name", "status", "review_notes"]
