"""Medicine + brand offerings (junction rows)."""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import logging

from app.repositories.medicine_brands_repository import MedicineBrandsRepository
from app.db.models import MedicineBrandOffering, Brand
from app.services.inventory_service import ensure_inventory_row
from app.schemas.medicine_brands_schema import (
    MedicineBrandCreateRequest,
    MedicineBrandUpdateRequest,
    MedicineBrandResponse,
)
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class MedicineBrandsService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(MedicineBrandsRepository(session), session)

    async def _brand_name(self, brand_id: UUID) -> str:
        r = await self.session.execute(select(Brand.name).where(Brand.id == brand_id, Brand.is_deleted == False))  # noqa: E712
        row = r.scalar_one_or_none()
        return row or "—"

    def _to_response(self, row: MedicineBrandOffering, brand_name: str) -> MedicineBrandResponse:
        d = self._model_to_dict(row)
        d["brand_name"] = brand_name
        return MedicineBrandResponse(**d)

    async def create_medicine_brand(
        self, data: MedicineBrandCreateRequest, created_by: UUID, created_ip: str
    ) -> MedicineBrandResponse:
        payload = data.model_dump()
        payload["is_active"] = True
        payload.setdefault("is_available", True)
        try:
            row = await self.repository.create(payload, created_by, created_ip)
        except IntegrityError as e:
            logger.warning("Offering create failed: %s", e)
            raise ValueError("Duplicate medicine+brand pair or invalid foreign key") from e
        await ensure_inventory_row(self.session, row.id, created_by, created_ip)
        name = await self._brand_name(row.brand_id)
        return self._to_response(row, name)

    async def update_medicine_brand(
        self, offering_id: UUID, data: MedicineBrandUpdateRequest, updated_by: UUID, updated_ip: str
    ) -> Optional[MedicineBrandResponse]:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        try:
            row = await self.repository.update(offering_id, update_data, updated_by, updated_ip)
        except IntegrityError as e:
            logger.warning("Offering update failed: %s", e)
            raise ValueError("Duplicate medicine+brand pair or invalid foreign key") from e
        if not row:
            return None
        name = await self._brand_name(row.brand_id)
        return self._to_response(row, name)

    async def delete_medicine_brand(self, offering_id: UUID, updated_by: UUID, updated_ip: str) -> bool:
        return await self.repository.soft_delete(offering_id, updated_by, updated_ip)
