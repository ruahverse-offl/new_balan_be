"""
Medicines Service
Business logic layer for medicines
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from sqlalchemy import select

from app.repositories.medicines_repository import MedicinesRepository
from app.schemas.medicines_schema import (
    MedicineCreateRequest,
    MedicineUpdateRequest,
    MedicineResponse,
    MedicineListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.db.models import TherapeuticCategory

logger = logging.getLogger(__name__)


async def _get_therapeutic_category_name(session, category_id) -> str:
    """Look up therapeutic category name by ID."""
    if not category_id:
        return "—"
    stmt = select(TherapeuticCategory.name).where(TherapeuticCategory.id == category_id)
    result = await session.execute(stmt)
    row = result.first()
    return (row[0] if row else None) or "—"


class MedicinesService(BaseService):
    """Service for medicines operations."""
    
    def __init__(self, session: AsyncSession):
        repository = MedicinesRepository(session)
        super().__init__(repository, session)
    
    async def create_medicine(
        self,
        data: MedicineCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> MedicineResponse:
        """Create a new medicine."""
        logger.info(f"Creating medicine: {data.name} with therapeutic_category_id={data.therapeutic_category_id}")
        medicine_data = data.model_dump()
        # Automatically set is_active to True
        medicine_data["is_active"] = True
        # Ensure therapeutic_category_id is included (required for medicines)
        if data.therapeutic_category_id:
            medicine_data["therapeutic_category_id"] = data.therapeutic_category_id
        medicine = await self.repository.create(medicine_data, created_by, created_ip)
        medicine_dict = self._model_to_dict(medicine)
        medicine_dict["therapeutic_category_name"] = await _get_therapeutic_category_name(self.session, medicine.therapeutic_category_id)
        return MedicineResponse(**medicine_dict)
    
    async def get_medicine_by_id(self, medicine_id: UUID) -> Optional[MedicineResponse]:
        """Get medicine by ID."""
        medicine = await self.repository.get_by_id(medicine_id)
        if not medicine:
            return None
        medicine_dict = self._model_to_dict(medicine)
        medicine_dict["therapeutic_category_name"] = await _get_therapeutic_category_name(self.session, medicine.therapeutic_category_id)
        return MedicineResponse(**medicine_dict)
    
    async def get_medicines_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> MedicineListResponse:
        """Get list of medicines with pagination, search, and sort."""
        medicines, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        category_ids = [m.therapeutic_category_id for m in medicines if m.therapeutic_category_id]
        name_by_category_id = {}
        if category_ids:
            stmt = select(TherapeuticCategory.id, TherapeuticCategory.name).where(
                TherapeuticCategory.id.in_(category_ids)
            )
            result = await self.session.execute(stmt)
            for row in result:
                name_by_category_id[str(row.id)] = row.name or "—"
        medicine_responses = []
        for m in medicines:
            d = self._model_to_dict(m)
            d["therapeutic_category_name"] = name_by_category_id.get(str(m.therapeutic_category_id), "—")
            medicine_responses.append(MedicineResponse(**d))
        return MedicineListResponse(
            items=medicine_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_medicine(
        self,
        medicine_id: UUID,
        data: MedicineUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[MedicineResponse]:
        """Update a medicine."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        logger.info(f"Updating medicine: {medicine_id} therapeutic_category_id={update_data.get('therapeutic_category_id')}")
        medicine = await self.repository.update(medicine_id, update_data, updated_by, updated_ip)
        if not medicine:
            return None
        medicine_dict = self._model_to_dict(medicine)
        medicine_dict["therapeutic_category_name"] = await _get_therapeutic_category_name(self.session, medicine.therapeutic_category_id)
        return MedicineResponse(**medicine_dict)
    
    async def delete_medicine(
        self,
        medicine_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a medicine."""
        logger.info(f"Deleting medicine: {medicine_id}")
        return await self.repository.soft_delete(medicine_id, updated_by, updated_ip)
