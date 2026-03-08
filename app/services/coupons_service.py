"""
Coupons Service
Business logic layer for coupons
"""

from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.db.models import Order
from app.repositories.coupons_repository import CouponsRepository
from app.schemas.coupons_schema import (
    CouponCreateRequest,
    CouponUpdateRequest,
    CouponResponse,
    CouponListResponse,
    CouponValidateRequest,
    CouponValidateResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CouponsService(BaseService):
    """Service for coupons operations."""
    
    def __init__(self, session: AsyncSession):
        repository = CouponsRepository(session)
        super().__init__(repository, session)
    
    async def create_coupon(
        self,
        data: CouponCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> CouponResponse:
        """Create a new coupon."""
        logger.info(f"Creating coupon: {data.code}")
        coupon_data = data.model_dump()
        coupon_data["code"] = coupon_data["code"].upper().strip()
        coupon_data["usage_count"] = 0
        coupon_data["is_active"] = True
        coupon = await self.repository.create(coupon_data, created_by, created_ip)
        coupon_dict = self._model_to_dict(coupon)
        return CouponResponse(**coupon_dict)
    
    async def get_coupon_by_id(self, coupon_id: UUID) -> Optional[CouponResponse]:
        """Get coupon by ID."""
        coupon = await self.repository.get_by_id(coupon_id)
        if not coupon:
            return None
        coupon_dict = self._model_to_dict(coupon)
        return CouponResponse(**coupon_dict)
    
    async def get_coupons_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> CouponListResponse:
        """Get list of coupons with pagination, search, and sort."""
        coupons, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters={"is_active": is_active} if is_active is not None else None
        )
        coupon_responses = [
            CouponResponse(**self._model_to_dict(c)) for c in coupons
        ]
        return CouponListResponse(
            items=coupon_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_coupon(
        self,
        coupon_id: UUID,
        data: CouponUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[CouponResponse]:
        """Update a coupon."""
        logger.info(f"Updating coupon: {coupon_id}")
        coupon_data = data.model_dump(exclude_unset=True)
        if "code" in coupon_data:
            coupon_data["code"] = coupon_data["code"].upper().strip()
        coupon = await self.repository.update(coupon_id, coupon_data, updated_by, updated_ip)
        if not coupon:
            return None
        coupon_dict = self._model_to_dict(coupon)
        return CouponResponse(**coupon_dict)
    
    async def delete_coupon(
        self,
        coupon_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a coupon."""
        logger.info(f"Deleting coupon: {coupon_id}")
        return await self.repository.soft_delete(coupon_id, updated_by, updated_ip)
    
    async def validate_coupon(self, data: CouponValidateRequest) -> CouponValidateResponse:
        """Validate a coupon code."""
        code = data.code.upper().strip()
        stmt = select(self.repository.model).where(
            self.repository.model.code == code,
            self.repository.model.is_deleted == False
        )
        result = await self.session.execute(stmt)
        coupon = result.scalar_one_or_none()
        
        if not coupon:
            return CouponValidateResponse(valid=False, message="Invalid coupon code")
        
        if not coupon.is_active:
            return CouponValidateResponse(valid=False, message="Coupon is disabled")
        
        if coupon.expiry_date and coupon.expiry_date < date.today():
            return CouponValidateResponse(valid=False, message="Coupon has expired")
        
        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            return CouponValidateResponse(valid=False, message="Coupon usage limit reached")
        
        if coupon.min_order_amount and data.order_amount < coupon.min_order_amount:
            return CouponValidateResponse(
                valid=False,
                message=f"Minimum order amount of ₹{coupon.min_order_amount} required"
            )
        
        # First-order-only: customer must have no previous orders
        first_order_only = getattr(coupon, "first_order_only", False)
        if first_order_only:
            customer_id = getattr(data, "customer_id", None)
            if not customer_id:
                return CouponValidateResponse(
                    valid=False,
                    message="This coupon is for first order only. Please log in to use it."
                )
            count_stmt = select(func.count()).select_from(Order).where(
                Order.customer_id == customer_id,
                Order.is_deleted == False
            )
            count_result = await self.session.execute(count_stmt)
            order_count = (count_result.scalar() or 0) or 0
            if order_count > 0:
                return CouponValidateResponse(
                    valid=False,
                    message="This coupon is valid only for your first order."
                )
        
        # Calculate discount
        discount_amount = (data.order_amount * coupon.discount_percentage / 100)
        if coupon.max_discount_amount:
            discount_amount = min(discount_amount, coupon.max_discount_amount)
        
        return CouponValidateResponse(
            valid=True,
            discount_amount=discount_amount,
            message="Coupon is valid"
        )
