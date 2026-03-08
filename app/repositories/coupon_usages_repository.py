"""
Coupon Usages Repository
Data access layer for coupon_usages
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import CouponUsage


class CouponUsagesRepository(BaseRepository[CouponUsage]):
    """Repository for coupon_usages table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CouponUsage, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for coupon usages."""
        return []
