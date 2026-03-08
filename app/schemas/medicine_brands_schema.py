"""
Medicine Brands Schema
Pydantic models for medicine_brands resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class MedicineBrandCreateRequest(BaseCreateRequest):
    """Request model for creating a medicine brand."""
    
    medicine_id: UUID = Field(..., description="Medicine ID")
    brand_name: str = Field(..., max_length=255, description="Brand name")
    manufacturer: str = Field(..., max_length=255, description="Manufacturer name")
    mrp: Decimal = Field(..., description="Maximum Retail Price (2 decimal places)")
    description: Optional[str] = Field(None, description="Brand description")
    # is_active is automatically set to True by the backend
    
    model_config = {"json_schema_extra": {"example": {
        "medicine_id": "m1e123-4567-8901-2345-678901234567",
        "brand_name": "Crocin",
        "manufacturer": "GSK",
        "mrp": 25.00,
        "description": "Paracetamol 500mg tablet"
    }}}


class MedicineBrandUpdateRequest(BaseUpdateRequest):
    """Request model for updating a medicine brand."""
    
    medicine_id: Optional[UUID] = Field(None, description="Medicine ID")
    brand_name: Optional[str] = Field(None, max_length=255, description="Brand name")
    manufacturer: Optional[str] = Field(None, max_length=255, description="Manufacturer name")
    mrp: Optional[Decimal] = Field(None, description="Maximum Retail Price (2 decimal places)")
    description: Optional[str] = Field(None, description="Brand description")
    is_active: Optional[bool] = Field(None, description="Whether the brand is active")
    
    model_config = {"json_schema_extra": {"example": {
        "brand_name": "Crocin Advance",
        "mrp": 30.00,
        "is_active": True
    }}}


class MedicineBrandResponse(BaseResponse):
    """Response model for medicine brand."""
    
    id: UUID = Field(..., description="Medicine Brand ID")
    medicine_id: UUID = Field(..., description="Medicine ID")
    medicine_name: Optional[str] = Field(None, description="Medicine name (included in list responses)")
    brand_name: str = Field(..., description="Brand name")
    manufacturer: str = Field(..., description="Manufacturer name")
    mrp: Decimal = Field(..., description="Maximum Retail Price")
    description: Optional[str] = Field(None, description="Brand description")
    is_active: bool = Field(..., description="Whether the brand is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "mb1e123-4567-8901-2345-678901234567",
        "medicine_id": "m1e123-4567-8901-2345-678901234567",
        "brand_name": "Crocin",
        "manufacturer": "GSK",
        "mrp": 25.00,
        "description": "Paracetamol 500mg tablet",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class MedicineBrandListResponse(ListResponse[MedicineBrandResponse]):
    """Response model for medicine brand list with pagination."""
    pass
