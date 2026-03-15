"""
Medicine Brands Router
FastAPI routes for medicine_brands resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.medicine_brands_service import MedicineBrandsService
from app.schemas.medicine_brands_schema import (
    MedicineBrandCreateRequest,
    MedicineBrandUpdateRequest,
    MedicineBrandResponse,
    MedicineBrandListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/medicine-brands", tags=["medicine-brands"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MedicineBrandResponse)
async def create_medicine_brand(
    data: MedicineBrandCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CREATE"))
):
    """Create a new medicine brand."""
    ip_address = get_client_ip(request)
    service = MedicineBrandsService(db)
    brand = await service.create_medicine_brand(data, current_user_id, ip_address)
    return brand


# List route MUST be before /{brand_id} so GET /api/v1/medicine-brands (no trailing slash) matches list, not path param
@router.get("/", response_model=MedicineBrandListResponse)
async def get_medicine_brands_list(
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    is_available: Optional[bool] = Query(default=None, description="Filter by availability (true = only available for customers)"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of medicine brands with pagination, search, and sort."""
    service = MedicineBrandsService(db)
    result = await service.get_medicine_brands_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        is_available=is_available
    )
    return result


@router.get("/{brand_id}", response_model=MedicineBrandResponse)
async def get_medicine_brand_by_id(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get medicine brand by ID."""
    service = MedicineBrandsService(db)
    brand = await service.get_medicine_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine brand with ID {brand_id} not found"
        )
    return brand


@router.patch("/{brand_id}", response_model=MedicineBrandResponse)
async def update_medicine_brand(
    brand_id: UUID,
    data: MedicineBrandUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_UPDATE"))
):
    """Update a medicine brand."""
    ip_address = get_client_ip(request)
    service = MedicineBrandsService(db)
    brand = await service.update_medicine_brand(brand_id, data, current_user_id, ip_address)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine brand with ID {brand_id} not found"
        )
    return brand


@router.delete("/{brand_id}", status_code=status.HTTP_200_OK)
async def delete_medicine_brand(
    brand_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_DELETE"))
):
    """Soft delete a medicine brand."""
    ip_address = get_client_ip(request)
    service = MedicineBrandsService(db)
    deleted = await service.delete_medicine_brand(brand_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine brand with ID {brand_id} not found"
        )
    return {"message": "Medicine brand deleted successfully", "id": str(brand_id)}
