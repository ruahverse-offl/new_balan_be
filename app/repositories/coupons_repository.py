"""
Coupons Repository
Data access layer for coupons
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Coupon


class CouponsRepository(BaseRepository[Coupon]):
    """Repository for coupons table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Coupon, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for coupons."""
        return ["code"]
