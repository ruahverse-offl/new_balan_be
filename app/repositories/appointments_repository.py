"""
Appointments Repository
Data access layer for appointments
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Appointment


class AppointmentsRepository(BaseRepository[Appointment]):
    """Repository for appointments table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Appointment, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for appointments."""
        return ["patient_name", "patient_phone", "status", "message", "notes"]
