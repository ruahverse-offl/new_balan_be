"""
Coupons Router
FastAPI routes for coupons resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.coupons_service import CouponsService
from app.schemas.coupons_schema import (
    CouponCreateRequest,
    CouponUpdateRequest,
    CouponResponse,
    CouponListResponse,
    CouponValidateRequest,
    CouponValidateResponse
)
from app.utils.auth import get_current_user_id_optional
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/coupons", tags=["coupons"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CouponResponse)
async def create_coupon(
    data: CouponCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Create a new coupon."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = CouponsService(db)
    coupon = await service.create_coupon(data, user_id, ip_address)
    return coupon


@router.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon_by_id(
    coupon_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get coupon by ID."""
    service = CouponsService(db)
    coupon = await service.get_coupon_by_id(coupon_id)
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon with ID {coupon_id} not found"
        )
    return coupon


@router.get("/", response_model=CouponListResponse)
async def get_coupons_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of coupons with pagination, search, and sort."""
    service = CouponsService(db)
    result = await service.get_coupons_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        is_active=is_active
    )
    return result


@router.patch("/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: UUID,
    data: CouponUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Update a coupon."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = CouponsService(db)
    coupon = await service.update_coupon(coupon_id, data, user_id, ip_address)
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon with ID {coupon_id} not found"
        )
    return coupon


@router.delete("/{coupon_id}", status_code=status.HTTP_200_OK)
async def delete_coupon(
    coupon_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Soft delete a coupon."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = CouponsService(db)
    deleted = await service.delete_coupon(coupon_id, user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon with ID {coupon_id} not found"
        )
    return {"message": "Coupon deleted successfully", "id": str(coupon_id)}


@router.post("/validate", response_model=CouponValidateResponse)
async def validate_coupon(
    data: CouponValidateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Validate a coupon code. Passes current user as customer_id for first-order-only checks."""
    # Inject logged-in customer for first-order-only validation
    if current_user_id is not None:
        data = CouponValidateRequest(
            code=data.code,
            order_amount=data.order_amount,
            customer_id=current_user_id
        )
    service = CouponsService(db)
    result = await service.validate_coupon(data)
    return result
