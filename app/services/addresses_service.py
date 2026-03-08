"""
Addresses Service
Business logic layer for addresses
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.addresses_repository import AddressesRepository
from app.schemas.addresses_schema import (
    AddressCreateRequest,
    AddressUpdateRequest,
    AddressResponse,
)
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class AddressesService(BaseService):
    """Service for addresses operations."""

    def __init__(self, session: AsyncSession):
        repository = AddressesRepository(session)
        super().__init__(repository, session)

    async def create_address(
        self,
        data: AddressCreateRequest,
        user_id: UUID,
        created_ip: str
    ) -> AddressResponse:
        """Create a new address for the current user."""
        logger.info(f"Creating address for user: {user_id}")
        address_data = data.model_dump()
        address_data["user_id"] = user_id

        if address_data.get("is_default"):
            await self.repository.clear_default_for_user(user_id)

        address = await self.repository.create(address_data, user_id, created_ip)
        return AddressResponse(**self._model_to_dict(address))

    async def get_my_addresses(self, user_id: UUID) -> List[AddressResponse]:
        """Get all addresses for the current user."""
        addresses = await self.repository.get_user_addresses(user_id)
        return [AddressResponse(**self._model_to_dict(a)) for a in addresses]

    async def update_address(
        self,
        address_id: UUID,
        data: AddressUpdateRequest,
        user_id: UUID,
        updated_ip: str
    ) -> Optional[AddressResponse]:
        """Update an address (only if owned by user)."""
        existing = await self.repository.get_by_id(address_id)
        if not existing or str(existing.user_id) != str(user_id):
            return None

        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if update_data.get("is_default"):
            await self.repository.clear_default_for_user(user_id)

        address = await self.repository.update(address_id, update_data, user_id, updated_ip)
        if not address:
            return None
        return AddressResponse(**self._model_to_dict(address))

    async def set_default(
        self,
        address_id: UUID,
        user_id: UUID,
        updated_ip: str
    ) -> Optional[AddressResponse]:
        """Mark an address as default (clears previous default)."""
        existing = await self.repository.get_by_id(address_id)
        if not existing or str(existing.user_id) != str(user_id):
            return None

        await self.repository.clear_default_for_user(user_id)
        address = await self.repository.update(
            address_id, {"is_default": True}, user_id, updated_ip
        )
        if not address:
            return None
        return AddressResponse(**self._model_to_dict(address))

    async def delete_address(
        self,
        address_id: UUID,
        user_id: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete an address (only if owned by user)."""
        existing = await self.repository.get_by_id(address_id)
        if not existing or str(existing.user_id) != str(user_id):
            return False
        logger.info(f"Deleting address: {address_id}")
        return await self.repository.soft_delete(address_id, user_id, updated_ip)
