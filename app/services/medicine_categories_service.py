"""Business logic for medicine_categories."""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.medicine_categories_repository import MedicineCategoriesRepository
from app.schemas.medicine_categories_schema import (
    MedicineCategoryCreateRequest,
    MedicineCategoryUpdateRequest,
    MedicineCategoryResponse,
    MedicineCategoryListResponse,
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class MedicineCategoriesService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(MedicineCategoriesRepository(session), session)

    async def create_category(
        self, data: MedicineCategoryCreateRequest, created_by: UUID, created_ip: str
    ) -> MedicineCategoryResponse:
        payload = data.model_dump()
        payload["is_active"] = True
        row = await self.repository.create(payload, created_by, created_ip)
        return MedicineCategoryResponse(**self._model_to_dict(row))

    async def get_category_by_id(self, category_id: UUID) -> Optional[MedicineCategoryResponse]:
        row = await self.repository.get_by_id(category_id)
        return MedicineCategoryResponse(**self._model_to_dict(row)) if row else None

    async def get_categories_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> MedicineCategoryListResponse:
        rows, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        return MedicineCategoryListResponse(
            items=[MedicineCategoryResponse(**self._model_to_dict(c)) for c in rows],
            pagination=PaginationResponse(**pagination),
        )

    async def update_category(
        self, category_id: UUID, data: MedicineCategoryUpdateRequest, updated_by: UUID, updated_ip: str
    ) -> Optional[MedicineCategoryResponse]:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        row = await self.repository.update(category_id, update_data, updated_by, updated_ip)
        return MedicineCategoryResponse(**self._model_to_dict(row)) if row else None

    async def delete_category(self, category_id: UUID, updated_by: UUID, updated_ip: str) -> bool:
        return await self.repository.soft_delete(category_id, updated_by, updated_ip)
