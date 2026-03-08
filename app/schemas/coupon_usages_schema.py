"""
Coupon Usages Schema
Pydantic models for coupon_usages resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class CouponUsageCreateRequest(BaseCreateRequest):
    """Request model for creating a coupon usage."""
    
    coupon_id: UUID = Field(..., description="Coupon ID")
    order_id: UUID = Field(..., description="Order ID")
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    discount_amount: Decimal = Field(..., description="Discount amount applied")
    # Snapshot fields — store at creation time for display on Coupon Usages page
    coupon_code: Optional[str] = Field(None, max_length=50)
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=15)
    order_final_amount: Optional[Decimal] = Field(None)
    
    model_config = {"json_schema_extra": {"example": {
        "coupon_id": "cp1e123-4567-8901-2345-678901234567",
        "order_id": "o1e123-4567-8901-2345-678901234567",
        "customer_id": "u123e456-7890-1234-5678-901234567890",
        "discount_amount": 15.00
    }}}


class CouponUsageResponse(BaseResponse):
    """Response model for coupon usage."""
    
    id: UUID = Field(..., description="Coupon usage ID")
    coupon_id: UUID = Field(..., description="Coupon ID")
    order_id: UUID = Field(..., description="Order ID")
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    discount_amount: Decimal = Field(..., description="Discount amount applied")
    # Enriched fields (for list display)
    coupon_code: Optional[str] = Field(None, description="Coupon code")
    order_customer_name: Optional[str] = Field(None, description="Order customer name")
    order_customer_phone: Optional[str] = Field(None, description="Order customer phone")
    order_final_amount: Optional[Decimal] = Field(None, description="Order final amount")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "cu1e123-4567-8901-2345-678901234567",
        "coupon_id": "cp1e123-4567-8901-2345-678901234567",
        "order_id": "o1e123-4567-8901-2345-678901234567",
        "customer_id": "u123e456-7890-1234-5678-901234567890",
        "discount_amount": 15.00,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class CouponUsageListResponse(ListResponse[CouponUsageResponse]):
    """Response model for coupon usage list with pagination."""
    pass
