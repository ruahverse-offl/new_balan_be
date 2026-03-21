"""
Order Items Schema
Pydantic models for order_items resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class OrderItemCreateRequest(BaseCreateRequest):
    """Request model for creating an order item."""
    
    order_id: UUID = Field(..., description="Order ID")
    medicine_brand_id: UUID = Field(..., description="Medicine brand ID")
    medicine_name: Optional[str] = Field(None, max_length=255, description="Medicine name snapshot")
    brand_name: Optional[str] = Field(None, max_length=255, description="Brand name snapshot")
    quantity: int = Field(..., ge=1, description="Quantity")
    unit_price: Decimal = Field(..., description="Unit price")
    total_price: Decimal = Field(..., description="Total price")
    requires_prescription: bool = Field(False, description="Whether prescription is required")
    
    model_config = {"json_schema_extra": {"example": {
        "order_id": "o1e123-4567-8901-2345-678901234567",
        "medicine_brand_id": "mb1e123-4567-8901-2345-678901234567",
        "quantity": 2,
        "unit_price": 45.00,
        "total_price": 90.00,
        "requires_prescription": False
    }}}


class OrderItemUpdateRequest(BaseUpdateRequest):
    """Request model for updating an order item."""
    
    order_id: Optional[UUID] = Field(None, description="Order ID")
    medicine_brand_id: Optional[UUID] = Field(None, description="Medicine brand ID")
    quantity: Optional[int] = Field(None, ge=1, description="Quantity")
    unit_price: Optional[Decimal] = Field(None, description="Unit price")
    total_price: Optional[Decimal] = Field(None, description="Total price")
    requires_prescription: Optional[bool] = Field(None, description="Whether prescription is required")
    
    model_config = {"json_schema_extra": {"example": {
        "quantity": 3,
        "total_price": 135.00
    }}}


class OrderItemResponse(BaseResponse):
    """Response model for order item."""
    
    id: UUID = Field(..., description="Order item ID")
    order_id: UUID = Field(..., description="Order ID")
    medicine_brand_id: UUID = Field(..., description="Medicine brand ID")
    medicine_name: Optional[str] = Field(None, description="Medicine name at order time")
    brand_name: Optional[str] = Field(None, description="Brand name at order time")
    quantity: int = Field(..., description="Quantity")
    unit_price: Decimal = Field(..., description="Unit price")
    total_price: Decimal = Field(..., description="Total price")
    requires_prescription: bool = Field(..., description="Whether prescription is required")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "oi1e123-4567-8901-2345-678901234567",
        "order_id": "o1e123-4567-8901-2345-678901234567",
        "medicine_brand_id": "mb1e123-4567-8901-2345-678901234567",
        "quantity": 2,
        "unit_price": 45.00,
        "total_price": 90.00,
        "requires_prescription": False,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class OrderItemListResponse(ListResponse[OrderItemResponse]):
    """Response model for order item list with pagination."""
    pass
