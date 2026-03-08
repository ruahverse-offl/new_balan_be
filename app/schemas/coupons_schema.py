"""
Coupons Schema
Pydantic models for coupons resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class CouponCreateRequest(BaseCreateRequest):
    """Request model for creating a coupon."""
    
    code: str = Field(..., max_length=50, description="Coupon code (unique, uppercase)")
    discount_percentage: Decimal = Field(..., ge=0, le=100, description="Discount percentage (0-100%)")
    expiry_date: Optional[date] = Field(None, description="Optional expiry date; after this date the coupon cannot be used")
    min_order_amount: Optional[Decimal] = Field(None, description="Minimum order amount")
    max_discount_amount: Optional[Decimal] = Field(None, description="Maximum discount cap")
    usage_limit: Optional[int] = Field(None, description="Total usage limit (null = unlimited)")
    first_order_only: Optional[bool] = Field(False, description="If True, coupon is valid only for a customer's first order")
    
    model_config = {"json_schema_extra": {"example": {
        "code": "SAVE5",
        "discount_percentage": 5.00,
        "expiry_date": "2026-03-15",
        "min_order_amount": 100.00,
        "max_discount_amount": 50.00,
        "usage_limit": 100
    }}}


class CouponUpdateRequest(BaseUpdateRequest):
    """Request model for updating a coupon."""
    
    code: Optional[str] = Field(None, max_length=50, description="Coupon code")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Discount percentage (0-100%)")
    expiry_date: Optional[date] = Field(None, description="Optional expiry date; after this date the coupon cannot be used")
    min_order_amount: Optional[Decimal] = Field(None, description="Minimum order amount")
    max_discount_amount: Optional[Decimal] = Field(None, description="Maximum discount cap")
    usage_limit: Optional[int] = Field(None, description="Total usage limit")
    is_active: Optional[bool] = Field(None, description="Whether the coupon is active")
    first_order_only: Optional[bool] = Field(None, description="If True, valid only for customer's first order")
    
    model_config = {"json_schema_extra": {"example": {
    "discount_percentage": 6.00,
        "is_active": True
    }}}


class CouponResponse(BaseResponse):
    """Response model for coupon."""
    
    id: UUID = Field(..., description="Coupon ID")
    code: str = Field(..., description="Coupon code")
    discount_percentage: Decimal = Field(..., description="Discount percentage")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    min_order_amount: Optional[Decimal] = Field(None, description="Minimum order amount")
    max_discount_amount: Optional[Decimal] = Field(None, description="Maximum discount cap")
    usage_limit: Optional[int] = Field(None, description="Total usage limit")
    usage_count: int = Field(..., description="Current usage count")
    is_active: bool = Field(..., description="Whether the coupon is active")
    first_order_only: bool = Field(False, description="If True, valid only for customer's first order")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "cp1e123-4567-8901-2345-678901234567",
        "code": "SAVE5",
        "discount_percentage": 5.00,
        "expiry_date": "2026-03-15",
        "min_order_amount": 100.00,
        "max_discount_amount": 50.00,
        "usage_limit": 100,
        "usage_count": 25,
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class CouponListResponse(ListResponse[CouponResponse]):
    """Response model for coupon list with pagination."""
    pass


class CouponValidateRequest(BaseModel):
    """Request model for validating a coupon."""
    
    code: str = Field(..., max_length=50, description="Coupon code to validate")
    order_amount: Decimal = Field(..., description="Order amount for validation")
    customer_id: Optional[UUID] = Field(None, description="Logged-in customer ID; required for first-order-only coupons")


class CouponValidateResponse(BaseModel):
    """Response model for coupon validation."""
    
    valid: bool = Field(..., description="Whether coupon is valid")
    discount_amount: Optional[Decimal] = Field(None, description="Discount amount if valid")
    message: str = Field(..., description="Validation message")
