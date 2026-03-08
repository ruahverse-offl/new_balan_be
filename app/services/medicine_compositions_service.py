"""
Medicine Compositions Service
Business logic layer for medicine_compositions
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.medicine_compositions_repository import MedicineCompositionsRepository
from app.schemas.medicine_compositions_schema import (
    MedicineCompositionCreateRequest,
    MedicineCompositionUpdateRequest,
    MedicineCompositionResponse,
    MedicineCompositionListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class MedicineCompositionsService(BaseService):
    """Service for medicine_compositions operations."""
    
    def __init__(self, session: AsyncSession):
        repository = MedicineCompositionsRepository(session)
        super().__init__(repository, session)
    
    async def create_medicine_composition(
        self,
        data: MedicineCompositionCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> MedicineCompositionResponse:
        """Create a new medicine composition."""
        logger.info(f"Creating medicine composition: {data.salt_name}")
        composition_data = data.model_dump()
        # Automatically set is_active to True
        composition_data["is_active"] = True
        composition = await self.repository.create(composition_data, created_by, created_ip)
        composition_dict = self._model_to_dict(composition)
        return MedicineCompositionResponse(**composition_dict)
    
    async def get_medicine_composition_by_id(self, composition_id: UUID) -> Optional[MedicineCompositionResponse]:
        """Get medicine composition by ID."""
        composition = await self.repository.get_by_id(composition_id)
        if not composition:
            return None
        composition_dict = self._model_to_dict(composition)
        return MedicineCompositionResponse(**composition_dict)
    
    async def get_medicine_compositions_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> MedicineCompositionListResponse:
        """Get list of medicine compositions with pagination, search, and sort."""
        compositions, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        composition_responses = [
            MedicineCompositionResponse(**self._model_to_dict(c)) for c in compositions
        ]
        return MedicineCompositionListResponse(
            items=composition_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_medicine_composition(
        self,
        composition_id: UUID,
        data: MedicineCompositionUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[MedicineCompositionResponse]:
        """Update a medicine composition."""
        logger.info(f"Updating medicine composition: {composition_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        composition = await self.repository.update(composition_id, update_data, updated_by, updated_ip)
        if not composition:
            return None
        composition_dict = self._model_to_dict(composition)
        return MedicineCompositionResponse(**composition_dict)
    
    async def delete_medicine_composition(
        self,
        composition_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a medicine composition."""
        logger.info(f"Deleting medicine composition: {composition_id}")
        return await self.repository.soft_delete(composition_id, updated_by, updated_ip)
