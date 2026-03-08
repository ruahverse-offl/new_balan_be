"""
Therapeutic Categories Router
FastAPI routes for therapeutic_categories resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.therapeutic_categories_service import TherapeuticCategoriesService
from app.schemas.therapeutic_categories_schema import (
    TherapeuticCategoryCreateRequest,
    TherapeuticCategoryUpdateRequest,
    TherapeuticCategoryResponse,
    TherapeuticCategoryListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/therapeutic-categories", tags=["therapeutic-categories"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TherapeuticCategoryResponse)
async def create_therapeutic_category(
    data: TherapeuticCategoryCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CATEGORY_MANAGE"))
):
    """Create a new therapeutic category."""
    ip_address = get_client_ip(request)
    service = TherapeuticCategoriesService(db)
    category = await service.create_therapeutic_category(data, current_user_id, ip_address)
    return category


@router.get("/{category_id}", response_model=TherapeuticCategoryResponse)
async def get_therapeutic_category_by_id(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get therapeutic category by ID."""
    service = TherapeuticCategoriesService(db)
    category = await service.get_therapeutic_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Therapeutic category with ID {category_id} not found"
        )
    return category


@router.get("/", response_model=TherapeuticCategoryListResponse)
async def get_therapeutic_categories_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of therapeutic categories with pagination, search, and sort."""
    service = TherapeuticCategoriesService(db)
    result = await service.get_therapeutic_categories_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )
    return result


@router.patch("/{category_id}", response_model=TherapeuticCategoryResponse)
async def update_therapeutic_category(
    category_id: UUID,
    data: TherapeuticCategoryUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CATEGORY_MANAGE"))
):
    """Update a therapeutic category."""
    ip_address = get_client_ip(request)
    service = TherapeuticCategoriesService(db)
    category = await service.update_therapeutic_category(category_id, data, current_user_id, ip_address)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Therapeutic category with ID {category_id} not found"
        )
    return category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_therapeutic_category(
    category_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CATEGORY_MANAGE"))
):
    """Soft delete a therapeutic category."""
    ip_address = get_client_ip(request)
    service = TherapeuticCategoriesService(db)
    deleted = await service.delete_therapeutic_category(category_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Therapeutic category with ID {category_id} not found"
        )
    return {"message": "Therapeutic category deleted successfully", "id": str(category_id)}
