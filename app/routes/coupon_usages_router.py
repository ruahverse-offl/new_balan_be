"""
Coupon Usages Router
FastAPI routes for coupon_usages resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.coupon_usages_service import CouponUsagesService
from app.schemas.coupon_usages_schema import (
    CouponUsageCreateRequest,
    CouponUsageResponse,
    CouponUsageListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/coupon-usages", tags=["coupon-usages"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CouponUsageResponse)
async def create_coupon_usage(
    data: CouponUsageCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("COUPON_CREATE"))
):
    """Create a new coupon usage."""
    ip_address = get_client_ip(request)
    service = CouponUsagesService(db)
    usage = await service.create_coupon_usage(data, current_user_id, ip_address)
    return usage


@router.get("/{usage_id}", response_model=CouponUsageResponse)
async def get_coupon_usage_by_id(
    usage_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("COUPON_VIEW"))
):
    """Get coupon usage by ID."""
    service = CouponUsagesService(db)
    usage = await service.get_coupon_usage_by_id(usage_id)
    if not usage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon usage with ID {usage_id} not found"
        )
    return usage


@router.get("/", response_model=CouponUsageListResponse)
async def get_coupon_usages_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    coupon_id: Optional[UUID] = Query(default=None),
    order_id: Optional[UUID] = Query(default=None),
    customer_id: Optional[UUID] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("COUPON_VIEW"))
):
    """Get list of coupon usages with pagination, search, and sort."""
    service = CouponUsagesService(db)
    result = await service.get_coupon_usages_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        coupon_id=coupon_id, order_id=order_id, customer_id=customer_id
    )
    return result
