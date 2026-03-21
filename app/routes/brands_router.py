"""CRUD for shared brand master."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.brands_service import BrandsService
from app.schemas.brands_schema import BrandCreateRequest, BrandUpdateRequest, BrandResponse, BrandListResponse
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/brands", tags=["brands"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BrandResponse)
async def create_brand(
    data: BrandCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CREATE")),
):
    ip_address = get_client_ip(request)
    service = BrandsService(db)
    try:
        return await service.create_brand(data, current_user_id, ip_address)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


# List route must be registered before GET /{brand_id} so `/brands` is not captured as a path param.
@router.get("/", response_model=BrandListResponse)
async def list_brands(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="name"),
    sort_order: Optional[str] = Query(default="asc", pattern="^(asc|desc)$"),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    service = BrandsService(db)
    return await service.get_brands_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order, is_active=is_active
    )


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand_by_id(brand_id: UUID, db: AsyncSession = Depends(get_db)):
    service = BrandsService(db)
    row = await service.get_brand_by_id(brand_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return row


@router.patch("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    data: BrandUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_UPDATE")),
):
    ip_address = get_client_ip(request)
    service = BrandsService(db)
    try:
        row = await service.update_brand(brand_id, data, current_user_id, ip_address)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return row


@router.delete("/{brand_id}", status_code=status.HTTP_200_OK)
async def delete_brand(
    brand_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_DELETE")),
):
    ip_address = get_client_ip(request)
    service = BrandsService(db)
    if not await service.delete_brand(brand_id, current_user_id, ip_address):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return {"message": "Brand deleted successfully", "id": str(brand_id)}
