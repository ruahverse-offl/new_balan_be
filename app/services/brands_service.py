"""Business logic for brands master."""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from app.repositories.brands_repository import BrandsRepository
from app.schemas.brands_schema import BrandCreateRequest, BrandUpdateRequest, BrandResponse, BrandListResponse
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class BrandsService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(BrandsRepository(session), session)

    async def create_brand(self, data: BrandCreateRequest, created_by: UUID, created_ip: str) -> BrandResponse:
        payload = data.model_dump()
        payload["is_active"] = True
        try:
            row = await self.repository.create(payload, created_by, created_ip)
        except IntegrityError as e:
            logger.warning("Brand create integrity error: %s", e)
            raise ValueError("A brand with this name already exists") from e
        return BrandResponse(**self._model_to_dict(row))

    async def get_brand_by_id(self, brand_id: UUID) -> Optional[BrandResponse]:
        row = await self.repository.get_by_id(brand_id)
        return BrandResponse(**self._model_to_dict(row)) if row else None

    async def get_brands_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> BrandListResponse:
        additional = {"is_active": is_active} if is_active is not None else None
        rows, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional,
        )
        return BrandListResponse(
            items=[BrandResponse(**self._model_to_dict(r)) for r in rows],
            pagination=PaginationResponse(**pagination),
        )

    async def update_brand(
        self, brand_id: UUID, data: BrandUpdateRequest, updated_by: UUID, updated_ip: str
    ) -> Optional[BrandResponse]:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        try:
            row = await self.repository.update(brand_id, update_data, updated_by, updated_ip)
        except IntegrityError as e:
            logger.warning("Brand update integrity error: %s", e)
            raise ValueError("A brand with this name already exists") from e
        return BrandResponse(**self._model_to_dict(row)) if row else None

    async def delete_brand(self, brand_id: UUID, updated_by: UUID, updated_ip: str) -> bool:
        return await self.repository.soft_delete(brand_id, updated_by, updated_ip)
