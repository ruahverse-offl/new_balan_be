"""
Test Bookings Repository
Data access layer for test_bookings
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import TestBooking


class TestBookingsRepository(BaseRepository[TestBooking]):
    """Repository for test_bookings table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TestBooking, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for test bookings."""
        return ["patient_name", "patient_phone", "status", "notes"]
