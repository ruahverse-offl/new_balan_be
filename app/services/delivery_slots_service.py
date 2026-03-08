"""
Delivery Slots Service
Business logic layer for delivery_slots
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.delivery_slots_repository import DeliverySlotsRepository
from app.schemas.delivery_slots_schema import (
    DeliverySlotCreateRequest,
    DeliverySlotUpdateRequest,
    DeliverySlotResponse,
    DeliverySlotListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class DeliverySlotsService(BaseService):
    """Service for delivery_slots operations."""
    
    def __init__(self, session: AsyncSession):
        repository = DeliverySlotsRepository(session)
        super().__init__(repository, session)
    
    async def create_delivery_slot(
        self,
        data: DeliverySlotCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> DeliverySlotResponse:
        """Create a new delivery slot."""
        logger.info(f"Creating delivery slot: {data.slot_time}")
        slot_data = data.model_dump()
        slot_data["is_active"] = True
        slot = await self.repository.create(slot_data, created_by, created_ip)
        slot_dict = self._model_to_dict(slot)
        return DeliverySlotResponse(**slot_dict)
    
    async def get_delivery_slot_by_id(self, slot_id: UUID) -> Optional[DeliverySlotResponse]:
        """Get delivery slot by ID."""
        slot = await self.repository.get_by_id(slot_id)
        if not slot:
            return None
        slot_dict = self._model_to_dict(slot)
        return DeliverySlotResponse(**slot_dict)
    
    async def get_delivery_slots_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        delivery_settings_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> DeliverySlotListResponse:
        """Get list of delivery slots with pagination, search, and sort."""
        additional_filters = {}
        if delivery_settings_id:
            additional_filters["delivery_settings_id"] = delivery_settings_id
        if is_active is not None:
            additional_filters["is_active"] = is_active
        
        slots, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional_filters if additional_filters else None
        )
        slot_responses = [
            DeliverySlotResponse(**self._model_to_dict(s)) for s in slots
        ]
        return DeliverySlotListResponse(
            items=slot_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_delivery_slot(
        self,
        slot_id: UUID,
        data: DeliverySlotUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[DeliverySlotResponse]:
        """Update a delivery slot."""
        logger.info(f"Updating delivery slot: {slot_id}")
        slot_data = data.model_dump(exclude_unset=True)
        slot = await self.repository.update(slot_id, slot_data, updated_by, updated_ip)
        if not slot:
            return None
        slot_dict = self._model_to_dict(slot)
        return DeliverySlotResponse(**slot_dict)
    
    async def delete_delivery_slot(
        self,
        slot_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a delivery slot."""
        logger.info(f"Deleting delivery slot: {slot_id}")
        return await self.repository.soft_delete(slot_id, updated_by, updated_ip)
