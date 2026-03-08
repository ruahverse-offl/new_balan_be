"""
Coupon Usages Service
Business logic layer for coupon_usages
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from sqlalchemy import select

from app.repositories.coupon_usages_repository import CouponUsagesRepository
from app.schemas.coupon_usages_schema import (
    CouponUsageCreateRequest,
    CouponUsageResponse,
    CouponUsageListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.db.models import Coupon, Order

logger = logging.getLogger(__name__)


class CouponUsagesService(BaseService):
    """Service for coupon_usages operations."""
    
    def __init__(self, session: AsyncSession):
        repository = CouponUsagesRepository(session)
        super().__init__(repository, session)
    
    async def create_coupon_usage(
        self,
        data: CouponUsageCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> CouponUsageResponse:
        """Create a new coupon usage."""
        logger.info(f"Creating coupon usage for order: {data.order_id}")
        usage_data = data.model_dump()
        usage = await self.repository.create(usage_data, created_by, created_ip)
        usage_dict = self._model_to_dict(usage)
        return CouponUsageResponse(**usage_dict)
    
    async def get_coupon_usage_by_id(self, usage_id: UUID) -> Optional[CouponUsageResponse]:
        """Get coupon usage by ID (with enriched coupon code and order details)."""
        usage = await self.repository.get_by_id(usage_id)
        if not usage:
            return None
        usage_dict = self._model_to_dict(usage)
        # Prefer stored snapshot; fall back to JOIN lookup
        usage_dict["coupon_code"] = (usage.coupon_code or "").strip() or None
        if not usage_dict["coupon_code"] and usage.coupon_id:
            stmt = select(Coupon.code).where(Coupon.id == usage.coupon_id)
            r = await self.session.execute(stmt)
            row = r.fetchone()
            usage_dict["coupon_code"] = row.code if row and row.code else "—"
        if not usage_dict["coupon_code"]:
            usage_dict["coupon_code"] = "—"
        if (usage.customer_name or "").strip() or (usage.customer_phone or "").strip() or usage.order_final_amount is not None:
            usage_dict["order_customer_name"] = (usage.customer_name or "").strip() or "—"
            usage_dict["order_customer_phone"] = (usage.customer_phone or "").strip() or "—"
            usage_dict["order_final_amount"] = usage.order_final_amount
        else:
            usage_dict["order_customer_name"] = "—"
            usage_dict["order_customer_phone"] = "—"
            usage_dict["order_final_amount"] = None
            if usage.order_id:
                stmt = select(Order.customer_name, Order.customer_phone, Order.final_amount).where(Order.id == usage.order_id)
                r = await self.session.execute(stmt)
                row = r.fetchone()
                if row:
                    usage_dict["order_customer_name"] = row.customer_name or "—"
                    usage_dict["order_customer_phone"] = row.customer_phone or "—"
                    usage_dict["order_final_amount"] = row.final_amount
        return CouponUsageResponse(**usage_dict)
    
    async def get_coupon_usages_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        coupon_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None
    ) -> CouponUsageListResponse:
        """Get list of coupon usages with pagination, search, and sort."""
        additional_filters = {}
        if coupon_id:
            additional_filters["coupon_id"] = coupon_id
        if order_id:
            additional_filters["order_id"] = order_id
        if customer_id:
            additional_filters["customer_id"] = customer_id
        
        usages, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional_filters if additional_filters else None
        )
        coupon_ids = [u.coupon_id for u in usages if u.coupon_id]
        order_ids = [u.order_id for u in usages if u.order_id]
        # Look up coupon codes and order details by ID (include soft-deleted so usages always show full data)
        code_by_coupon_id = {}
        if coupon_ids:
            stmt = select(Coupon.id, Coupon.code).where(Coupon.id.in_(coupon_ids))
            result = await self.session.execute(stmt)
            for row in result:
                code_by_coupon_id[str(row.id)] = row.code or "—"
        order_info_by_id = {}
        if order_ids:
            stmt = select(
                Order.id,
                Order.customer_name,
                Order.customer_phone,
                Order.final_amount
            ).where(Order.id.in_(order_ids))
            result = await self.session.execute(stmt)
            for row in result:
                order_info_by_id[str(row.id)] = {
                    "customer_name": row.customer_name if row.customer_name else "—",
                    "customer_phone": row.customer_phone if row.customer_phone else "—",
                    "final_amount": row.final_amount,
                }
        usage_responses = []
        for u in usages:
            d = self._model_to_dict(u)
            # Prefer stored snapshot (saved at order time); fall back to JOIN lookup for legacy rows
            d["coupon_code"] = (u.coupon_code or "").strip() or code_by_coupon_id.get(str(u.coupon_id), "—")
            if (u.customer_name or "").strip() or (u.customer_phone or "").strip() or u.order_final_amount is not None:
                d["order_customer_name"] = (u.customer_name or "").strip() or "—"
                d["order_customer_phone"] = (u.customer_phone or "").strip() or "—"
                d["order_final_amount"] = u.order_final_amount
            else:
                order_info = order_info_by_id.get(str(u.order_id), {})
                d["order_customer_name"] = order_info.get("customer_name", "—")
                d["order_customer_phone"] = order_info.get("customer_phone", "—")
                d["order_final_amount"] = order_info.get("final_amount")
            usage_responses.append(CouponUsageResponse(**d))
        return CouponUsageListResponse(
            items=usage_responses,
            pagination=PaginationResponse(**pagination)
        )
