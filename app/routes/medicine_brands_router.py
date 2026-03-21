"""
Medicine Brands Router
Staff-only create/update/delete for medicine_brands.
Listing and read-by-id are served via GET /medicines?include_brands=true and GET /medicines/{id}.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.medicine_brands_service import MedicineBrandsService
from app.schemas.medicine_brands_schema import (
    MedicineBrandCreateRequest,
    MedicineBrandUpdateRequest,
    MedicineBrandResponse,
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/medicine-brands", tags=["medicine-brands"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MedicineBrandResponse)
async def create_medicine_brand(
    data: MedicineBrandCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CREATE")),
):
    """Create a new medicine brand."""
    ip_address = get_client_ip(request)
    service = MedicineBrandsService(db)
    try:
        brand = await service.create_medicine_brand(data, current_user_id, ip_address)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return brand


@router.patch("/{brand_id}", response_model=MedicineBrandResponse)
async def update_medicine_brand(
    brand_id: UUID,
    data: MedicineBrandUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_UPDATE")),
):
    """Update a medicine brand."""
    ip_address = get_client_ip(request)
    service = MedicineBrandsService(db)
    try:
        brand = await service.update_medicine_brand(brand_id, data, current_user_id, ip_address)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine brand with ID {brand_id} not found",
        )
    return brand


@router.delete("/{brand_id}", status_code=status.HTTP_200_OK)
async def delete_medicine_brand(
    brand_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_DELETE")),
):
    """Soft delete a medicine brand."""
    ip_address = get_client_ip(request)
    service = MedicineBrandsService(db)
    deleted = await service.delete_medicine_brand(brand_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine brand with ID {brand_id} not found",
        )
    return {"message": "Medicine brand deleted successfully", "id": str(brand_id)}
