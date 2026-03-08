"""
Delivery Settings Schema
Pydantic models for delivery_settings resource
"""

from typing import Optional, List, Dict, Any
from pydantic import Field, BaseModel, field_serializer
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.schemas.common import BaseCreateRequest, BaseUpdateRequest, BaseResponse


class DeliveryZone(BaseModel):
    """Delivery zone configuration."""
    zone_name: str
    delivery_fee: Decimal
    free_delivery_threshold: Decimal


class DeliverySettingCreateRequest(BaseCreateRequest):
    """Request model for creating delivery settings."""
    
    is_enabled: bool = Field(True, description="Whether delivery is enabled")
    min_order_amount: Decimal = Field(..., description="Minimum order amount")
    delivery_fee: Decimal = Field(..., description="Delivery fee")
    free_delivery_threshold: Decimal = Field(..., description="Free delivery threshold")
    delivery_zones: Optional[List[DeliveryZone]] = Field(None, description="Delivery zones configuration")
    show_marquee: bool = Field(True, description="Show marquee on frontend")
    
    model_config = {"json_schema_extra": {"example": {
        "is_enabled": True,
        "min_order_amount": 200.00,
        "delivery_fee": 50.00,
        "free_delivery_threshold": 500.00,
        "delivery_zones": [
            {
                "zone_name": "Thoothukudi City",
                "delivery_fee": 50.00,
                "free_delivery_threshold": 500.00
            }
        ],
        "show_marquee": True
    }}}


class DeliverySettingUpdateRequest(BaseUpdateRequest):
    """Request model for updating delivery settings."""
    
    is_enabled: Optional[bool] = Field(None, description="Whether delivery is enabled")
    min_order_amount: Optional[Decimal] = Field(None, description="Minimum order amount")
    delivery_fee: Optional[Decimal] = Field(None, description="Delivery fee")
    free_delivery_threshold: Optional[Decimal] = Field(None, description="Free delivery threshold")
    delivery_zones: Optional[List[DeliveryZone]] = Field(None, description="Delivery zones configuration")
    show_marquee: Optional[bool] = Field(None, description="Show marquee on frontend")
    is_active: Optional[bool] = Field(None, description="Whether the settings are active")
    
    model_config = {"json_schema_extra": {"example": {
        "delivery_fee": 60.00,
        "show_marquee": False
    }}}


class DeliverySettingResponse(BaseResponse):
    """Response model for delivery settings."""
    
    id: UUID = Field(..., description="Settings ID")
    is_enabled: bool = Field(..., description="Whether delivery is enabled")
    min_order_amount: Decimal = Field(..., description="Minimum order amount")
    delivery_fee: Decimal = Field(..., description="Delivery fee")
    free_delivery_threshold: Decimal = Field(..., description="Free delivery threshold")
    delivery_zones: Optional[List[Dict[str, Any]]] = Field(None, description="Delivery zones configuration (JSON)")
    show_marquee: bool = Field(..., description="Show marquee on frontend")
    is_active: bool = Field(..., description="Whether the settings are active")

    @field_serializer("min_order_amount", "delivery_fee", "free_delivery_threshold")
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[float]:
        """Serialize Decimal to float for JSON (avoid 'Decimal is not JSON serializable')."""
        return float(v) if v is not None else None

    model_config = {"json_schema_extra": {"example": {
        "id": "ds1e123-4567-8901-2345-678901234567",
        "is_enabled": True,
        "min_order_amount": 200.00,
        "delivery_fee": 50.00,
        "free_delivery_threshold": 500.00,
        "delivery_zones": [
            {
                "zone_name": "Thoothukudi City",
                "delivery_fee": 50.00,
                "free_delivery_threshold": 500.00
            }
        ],
        "show_marquee": True,
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}
