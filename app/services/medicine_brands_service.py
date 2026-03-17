"""
Medicine Brands Service
Business logic layer for medicine_brands
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from fastapi import HTTPException, status

from app.repositories.medicine_brands_repository import MedicineBrandsRepository
from app.repositories.medicines_repository import MedicinesRepository
from app.schemas.medicine_brands_schema import (
    MedicineBrandCreateRequest,
    MedicineBrandUpdateRequest,
    MedicineBrandResponse,
    MedicineBrandListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.db.models import Medicine

logger = logging.getLogger(__name__)


class MedicineBrandsService(BaseService):
    """Service for medicine_brands operations."""
    
    def __init__(self, session: AsyncSession):
        repository = MedicineBrandsRepository(session)
        super().__init__(repository, session)
    
    async def create_medicine_brand(
        self,
        data: MedicineBrandCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> MedicineBrandResponse:
        """Create a new medicine brand."""
        logger.info(f"Creating medicine brand: {data.brand_name}")
        brand_data = data.model_dump()
        # Automatically set is_active to True
        brand_data["is_active"] = True
        brand_data.setdefault("is_available", True)
        brand = await self.repository.create(brand_data, created_by, created_ip)
        brand_dict = self._model_to_dict(brand)
        return MedicineBrandResponse(**brand_dict)
    
    async def get_medicine_brand_by_id(self, brand_id: UUID) -> Optional[MedicineBrandResponse]:
        """Get medicine brand by ID."""
        brand = await self.repository.get_by_id(brand_id)
        if not brand:
            return None
        brand_dict = self._model_to_dict(brand)
        return MedicineBrandResponse(**brand_dict)
    
    async def get_medicine_brands_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        is_available: Optional[bool] = None
    ) -> MedicineBrandListResponse:
        """Get list of medicine brands with pagination, search, and sort. Filter by is_available for customer-facing lists."""
        additional = {"is_available": is_available} if is_available is not None else None
        brands, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional
        )
        medicine_ids = [b.medicine_id for b in brands if b.medicine_id]
        name_by_id = {}
        if medicine_ids:
            stmt = select(Medicine.id, Medicine.name).where(Medicine.id.in_(medicine_ids))
            result = await self.session.execute(stmt)
            for row in result:
                name_by_id[str(row.id)] = row.name or "—"
        brand_responses = []
        for b in brands:
            d = self._model_to_dict(b)
            d["medicine_name"] = name_by_id.get(str(b.medicine_id), "—")
            brand_responses.append(MedicineBrandResponse(**d))
        return MedicineBrandListResponse(
            items=brand_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_medicine_brand(
        self,
        brand_id: UUID,
        data: MedicineBrandUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[MedicineBrandResponse]:
        """Update a medicine brand. When is_available is set to True, parent medicine becomes available."""
        logger.info(f"Updating medicine brand: {brand_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        # Validation: cannot mark a brand available if its parent medicine is inactive/deleted
        if update_data.get("is_available") is True:
            existing = await self.repository.get_by_id(brand_id)
            if not existing:
                return None
            if existing.medicine_id:
                med_row = await self.session.execute(
                    select(Medicine).where(Medicine.id == existing.medicine_id, Medicine.is_deleted == False)
                )
                med = med_row.scalar_one_or_none()
                if not med or med.is_active is False:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot mark brand as available because the parent medicine is inactive or deleted.",
                    )

        brand = await self.repository.update(brand_id, update_data, updated_by, updated_ip)
        if not brand:
            return None
        if update_data.get("is_available") is True and brand.medicine_id:
            medicines_repo = MedicinesRepository(self.session)
            await medicines_repo.update(brand.medicine_id, {"is_available": True}, updated_by, updated_ip)
            logger.info(f"Set parent medicine {brand.medicine_id} is_available=True (brand {brand_id} is available)")
        brand_dict = self._model_to_dict(brand)
        return MedicineBrandResponse(**brand_dict)
    
    async def delete_medicine_brand(
        self,
        brand_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a medicine brand."""
        logger.info(f"Deleting medicine brand: {brand_id}")
        return await self.repository.soft_delete(brand_id, updated_by, updated_ip)
