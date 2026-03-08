"""
Therapeutic Categories Service
Business logic layer for therapeutic_categories
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.therapeutic_categories_repository import TherapeuticCategoriesRepository
from app.schemas.therapeutic_categories_schema import (
    TherapeuticCategoryCreateRequest,
    TherapeuticCategoryUpdateRequest,
    TherapeuticCategoryResponse,
    TherapeuticCategoryListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class TherapeuticCategoriesService(BaseService):
    """Service for therapeutic_categories operations."""
    
    def __init__(self, session: AsyncSession):
        repository = TherapeuticCategoriesRepository(session)
        super().__init__(repository, session)
    
    async def create_therapeutic_category(
        self,
        data: TherapeuticCategoryCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> TherapeuticCategoryResponse:
        """Create a new therapeutic category."""
        logger.info(f"Creating therapeutic category: {data.name}")
        category_data = data.model_dump()
        # Automatically set is_active to True
        category_data["is_active"] = True
        category = await self.repository.create(category_data, created_by, created_ip)
        category_dict = self._model_to_dict(category)
        return TherapeuticCategoryResponse(**category_dict)
    
    async def get_therapeutic_category_by_id(self, category_id: UUID) -> Optional[TherapeuticCategoryResponse]:
        """Get therapeutic category by ID."""
        category = await self.repository.get_by_id(category_id)
        if not category:
            return None
        category_dict = self._model_to_dict(category)
        return TherapeuticCategoryResponse(**category_dict)
    
    async def get_therapeutic_categories_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> TherapeuticCategoryListResponse:
        """Get list of therapeutic categories with pagination, search, and sort."""
        categories, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        category_responses = [
            TherapeuticCategoryResponse(**self._model_to_dict(c)) for c in categories
        ]
        return TherapeuticCategoryListResponse(
            items=category_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_therapeutic_category(
        self,
        category_id: UUID,
        data: TherapeuticCategoryUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[TherapeuticCategoryResponse]:
        """Update a therapeutic category."""
        logger.info(f"Updating therapeutic category: {category_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        category = await self.repository.update(category_id, update_data, updated_by, updated_ip)
        if not category:
            return None
        category_dict = self._model_to_dict(category)
        return TherapeuticCategoryResponse(**category_dict)
    
    async def delete_therapeutic_category(
        self,
        category_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a therapeutic category."""
        logger.info(f"Deleting therapeutic category: {category_id}")
        return await self.repository.soft_delete(category_id, updated_by, updated_ip)
