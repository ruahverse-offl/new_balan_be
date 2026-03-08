"""
Product Categories Router
FastAPI routes for product_categories resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.product_categories_service import ProductCategoriesService
from app.schemas.product_categories_schema import (
    ProductCategoryCreateRequest,
    ProductCategoryUpdateRequest,
    ProductCategoryResponse,
    ProductCategoryListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/product-categories", tags=["product-categories"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductCategoryResponse)
async def create_product_category(
    data: ProductCategoryCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CATEGORY_MANAGE"))
):
    """Create a new product category."""
    ip_address = get_client_ip(request)
    service = ProductCategoriesService(db)
    category = await service.create_product_category(data, current_user_id, ip_address)
    return category


@router.get("/{category_id}", response_model=ProductCategoryResponse)
async def get_product_category_by_id(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get product category by ID."""
    service = ProductCategoriesService(db)
    category = await service.get_product_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category with ID {category_id} not found"
        )
    return category


@router.get("/", response_model=ProductCategoryListResponse)
async def get_product_categories_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of product categories with pagination, search, and sort."""
    service = ProductCategoriesService(db)
    result = await service.get_product_categories_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        is_active=is_active
    )
    return result


@router.patch("/{category_id}", response_model=ProductCategoryResponse)
async def update_product_category(
    category_id: UUID,
    data: ProductCategoryUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CATEGORY_MANAGE"))
):
    """Update a product category."""
    ip_address = get_client_ip(request)
    service = ProductCategoriesService(db)
    category = await service.update_product_category(category_id, data, current_user_id, ip_address)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category with ID {category_id} not found"
        )
    return category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_product_category(
    category_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CATEGORY_MANAGE"))
):
    """Soft delete a product category."""
    ip_address = get_client_ip(request)
    service = ProductCategoriesService(db)
    deleted = await service.delete_product_category(category_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category with ID {category_id} not found"
        )
    return {"message": "Product category deleted successfully", "id": str(category_id)}
