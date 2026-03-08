"""
Delivery Slots Repository
Data access layer for delivery_slots
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import DeliverySlot


class DeliverySlotsRepository(BaseRepository[DeliverySlot]):
    """Repository for delivery_slots table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(DeliverySlot, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for delivery slots."""
        return ["slot_time"]
