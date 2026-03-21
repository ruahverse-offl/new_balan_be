"""
Delivery Settings Repository
Data access layer for delivery_settings
"""

from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base_repository import BaseRepository
from app.db.models import DeliverySetting


# Defaults for required columns when creating singleton via PATCH (no row exists yet)
_DELIVERY_SETTINGS_CREATE_DEFAULTS = {
    "is_enabled": True,
    "min_order_amount": Decimal("0"),
    "delivery_fee": Decimal("40"),
    "free_delivery_threshold": Decimal("500"),
    "free_delivery_max_amount": None,
    "show_marquee": True,
    "is_active": True,
}


class DeliverySettingsRepository(BaseRepository[DeliverySetting]):
    """Repository for delivery_settings table (Singleton pattern)."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(DeliverySetting, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for delivery settings."""
        return []
    
    async def get_singleton(self) -> Optional[DeliverySetting]:
        """Get the single delivery settings record (uses first row if multiple exist)."""
        stmt = select(self.model).where(self.model.is_deleted == False)
        result = await self.session.execute(stmt)
        row = result.scalars().first()
        return row
    
    async def create_or_update(
        self,
        data: dict,
        created_by: UUID,
        created_ip: str,
        updated_by: Optional[UUID] = None,
        updated_ip: Optional[str] = None
    ) -> DeliverySetting:
        """Create or update the singleton delivery settings."""
        existing = await self.get_singleton()
        if existing:
            # Update existing
            if updated_by is None:
                updated_by = created_by
            if updated_ip is None:
                updated_ip = created_ip
            return await self.update(existing.id, data, updated_by, updated_ip)
        else:
            # Create new: merge with defaults so required columns are set (PATCH may send partial data)
            create_data = {**_DELIVERY_SETTINGS_CREATE_DEFAULTS, **data}
            return await self.create(create_data, created_by, created_ip)
