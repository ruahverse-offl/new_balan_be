"""
Pydantic models for delivery_settings resource.

Admin-facing fields are **free_delivery_min_amount** and **free_delivery_max_amount** (free delivery band).
The database still stores the lower bound in ``free_delivery_threshold``; the service maps aliases.
Other columns (delivery fee, min order, slots JSON, etc.) remain for backward compatibility and checkout math.
"""

from typing import Optional, List, Dict, Any
from pydantic import Field, field_serializer
from decimal import Decimal
from uuid import UUID

from app.schemas.common import BaseCreateRequest, BaseUpdateRequest, BaseResponse


class DeliverySettingCreateRequest(BaseCreateRequest):
    """Create singleton delivery settings (usually via repository defaults + PATCH)."""

    is_enabled: bool = Field(True, description="Whether home delivery is enabled")
    min_order_amount: Decimal = Field(Decimal("0"), description="Minimum order subtotal (legacy; default 0)")
    delivery_fee: Decimal = Field(Decimal("40"), description="Fee when outside free-delivery band")
    free_delivery_min_amount: Decimal = Field(
        Decimal("500"),
        description="Minimum cart subtotal (₹) to qualify for free delivery",
    )
    free_delivery_max_amount: Optional[Decimal] = Field(
        None,
        description="If set and > 0, free delivery only when subtotal <= this amount; omit or 0 for no upper cap",
    )
    show_marquee: bool = Field(True, description="Show coupon marquee on storefront")
    delivery_zones: Optional[List[Dict[str, Any]]] = Field(None, description="Legacy JSON; optional")
    delivery_slot_times: Optional[List[Dict[str, Any]]] = Field(None, description="Legacy slot JSON; optional")

    model_config = {
        "json_schema_extra": {
            "example": {
                "is_enabled": True,
                "min_order_amount": 0,
                "delivery_fee": 40,
                "free_delivery_min_amount": 500,
                "free_delivery_max_amount": 10000,
                "show_marquee": True,
            }
        }
    }


class DeliverySettingUpdateRequest(BaseUpdateRequest):
    """Partial update; admin typically sends only free-delivery min/max."""

    is_enabled: Optional[bool] = None
    min_order_amount: Optional[Decimal] = None
    delivery_fee: Optional[Decimal] = None
    free_delivery_min_amount: Optional[Decimal] = Field(
        None,
        description="Minimum cart subtotal (₹) for free delivery",
    )
    free_delivery_max_amount: Optional[Decimal] = Field(
        None,
        description="Maximum cart subtotal (₹) for free delivery; null = no upper limit",
    )
    delivery_zones: Optional[List[Dict[str, Any]]] = None
    show_marquee: Optional[bool] = None
    delivery_slot_times: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

    model_config = {"json_schema_extra": {"example": {"free_delivery_min_amount": 500, "free_delivery_max_amount": 10000}}}


class DeliverySettingResponse(BaseResponse):
    """API response including aliases for free-delivery band."""

    id: UUID = Field(..., description="Settings ID")
    is_enabled: bool = Field(..., description="Whether delivery is enabled")
    min_order_amount: Decimal = Field(..., description="Minimum order subtotal")
    delivery_fee: Decimal = Field(..., description="Delivery fee when not free")
    free_delivery_threshold: Decimal = Field(
        ...,
        description="DB column: same as free_delivery_min_amount",
    )
    free_delivery_min_amount: Decimal = Field(
        ...,
        description="Minimum subtotal (₹) for free delivery",
    )
    free_delivery_max_amount: Optional[Decimal] = Field(
        None,
        description="Max subtotal (₹) for free delivery if set",
    )
    delivery_zones: Optional[List[Dict[str, Any]]] = None
    show_marquee: bool = Field(..., description="Show marquee on frontend")
    is_active: bool = Field(..., description="Whether the settings row is active")
    delivery_slot_times: Optional[List[Dict[str, Any]]] = None

    @field_serializer(
        "min_order_amount",
        "delivery_fee",
        "free_delivery_threshold",
        "free_delivery_min_amount",
        "free_delivery_max_amount",
    )
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[float]:
        return float(v) if v is not None else None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "ds1e123-4567-8901-2345-678901234567",
                "is_enabled": True,
                "min_order_amount": 0,
                "delivery_fee": 40,
                "free_delivery_threshold": 500,
                "free_delivery_min_amount": 500,
                "free_delivery_max_amount": 10000,
                "show_marquee": True,
                "is_active": True,
                "delivery_slot_times": [],
            }
        }
    }
