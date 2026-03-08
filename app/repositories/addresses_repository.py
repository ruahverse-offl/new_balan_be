"""
Addresses Repository
Data access layer for addresses
"""

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.repositories.base_repository import BaseRepository
from app.db.models import Address


class AddressesRepository(BaseRepository[Address]):
    """Repository for addresses table."""

    def __init__(self, session: AsyncSession):
        super().__init__(Address, session)

    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for addresses."""
        return ["label", "street", "city", "state", "pincode"]

    async def clear_default_for_user(self, user_id: UUID) -> None:
        """Set is_default=False for all addresses of a given user."""
        stmt = (
            update(Address)
            .where(
                and_(
                    Address.user_id == user_id,
                    Address.is_deleted == False,
                    Address.is_default == True
                )
            )
            .values(is_default=False)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_user_addresses(self, user_id: UUID) -> List[Address]:
        """Get all active, non-deleted addresses for a user, default first."""
        stmt = (
            select(Address)
            .where(
                and_(
                    Address.user_id == user_id,
                    Address.is_deleted == False,
                    Address.is_active == True
                )
            )
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
