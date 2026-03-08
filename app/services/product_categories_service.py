"""
Product Categories Service
Business logic layer for product_categories
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.product_categories_repository import ProductCategoriesRepository
from app.schemas.product_categories_schema import (
    ProductCategoryCreateRequest,
    ProductCategoryUpdateRequest,
    ProductCategoryResponse,
    ProductCategoryListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class ProductCategoriesService(BaseService):
    """Service for product_categories operations."""
    
    def __init__(self, session: AsyncSession):
        repository = ProductCategoriesRepository(session)
        super().__init__(repository, session)
    
    async def create_product_category(
        self,
        data: ProductCategoryCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> ProductCategoryResponse:
        """Create a new product category."""
        logger.info(f"Creating product category: {data.name}")
        category_data = data.model_dump()
        category_data["is_active"] = True
        category = await self.repository.create(category_data, created_by, created_ip)
        category_dict = self._model_to_dict(category)
        return ProductCategoryResponse(**category_dict)
    
    async def get_product_category_by_id(self, category_id: UUID) -> Optional[ProductCategoryResponse]:
        """Get product category by ID."""
        category = await self.repository.get_by_id(category_id)
        if not category:
            return None
        category_dict = self._model_to_dict(category)
        return ProductCategoryResponse(**category_dict)
    
    async def get_product_categories_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> ProductCategoryListResponse:
        """Get list of product categories with pagination, search, and sort."""
        categories, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters={"is_active": is_active} if is_active is not None else None
        )
        category_responses = [
            ProductCategoryResponse(**self._model_to_dict(c)) for c in categories
        ]
        return ProductCategoryListResponse(
            items=category_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_product_category(
        self,
        category_id: UUID,
        data: ProductCategoryUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[ProductCategoryResponse]:
        """Update a product category."""
        logger.info(f"Updating product category: {category_id}")
        category_data = data.model_dump(exclude_unset=True)
        category = await self.repository.update(category_id, category_data, updated_by, updated_ip)
        if not category:
            return None
        category_dict = self._model_to_dict(category)
        return ProductCategoryResponse(**category_dict)
    
    async def delete_product_category(
        self,
        category_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a product category."""
        logger.info(f"Deleting product category: {category_id}")
        return await self.repository.soft_delete(category_id, updated_by, updated_ip)
