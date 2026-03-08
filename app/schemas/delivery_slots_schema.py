"""
Delivery Slots Schema
Pydantic models for delivery_slots resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class DeliverySlotCreateRequest(BaseCreateRequest):
    """Request model for creating a delivery slot."""
    
    delivery_settings_id: UUID = Field(..., description="Delivery settings ID")
    slot_time: str = Field(..., max_length=100, description="Slot time")
    slot_order: int = Field(..., description="Slot order for sorting")
    
    model_config = {"json_schema_extra": {"example": {
        "delivery_settings_id": "ds1e123-4567-8901-2345-678901234567",
        "slot_time": "10:00 AM - 12:00 PM",
        "slot_order": 1
    }}}


class DeliverySlotUpdateRequest(BaseUpdateRequest):
    """Request model for updating a delivery slot."""
    
    delivery_settings_id: Optional[UUID] = Field(None, description="Delivery settings ID")
    slot_time: Optional[str] = Field(None, max_length=100, description="Slot time")
    slot_order: Optional[int] = Field(None, description="Slot order for sorting")
    is_active: Optional[bool] = Field(None, description="Whether the slot is active")
    
    model_config = {"json_schema_extra": {"example": {
        "slot_time": "10:00 AM - 1:00 PM",
        "is_active": True
    }}}


class DeliverySlotResponse(BaseResponse):
    """Response model for delivery slot."""
    
    id: UUID = Field(..., description="Slot ID")
    delivery_settings_id: UUID = Field(..., description="Delivery settings ID")
    slot_time: str = Field(..., description="Slot time")
    slot_order: int = Field(..., description="Slot order for sorting")
    is_active: bool = Field(..., description="Whether the slot is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "dls1e123-4567-8901-2345-678901234567",
        "delivery_settings_id": "ds1e123-4567-8901-2345-678901234567",
        "slot_time": "10:00 AM - 12:00 PM",
        "slot_order": 1,
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class DeliverySlotListResponse(ListResponse[DeliverySlotResponse]):
    """Response model for delivery slot list with pagination."""
    pass
