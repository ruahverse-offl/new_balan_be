"""
Medicine Compositions Schema
Pydantic models for medicine_compositions resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class MedicineCompositionCreateRequest(BaseCreateRequest):
    """Request model for creating a medicine composition."""
    
    medicine_id: UUID = Field(..., description="Medicine ID")
    salt_name: str = Field(..., max_length=255, description="Salt name")
    strength: str = Field(..., max_length=50, description="Strength value")
    unit: str = Field(..., max_length=20, description="Unit of measurement")
    # is_active is automatically set to True by the backend
    
    model_config = {"json_schema_extra": {"example": {
        "medicine_id": "m1e123-4567-8901-2345-678901234567",
        "salt_name": "Paracetamol",
        "strength": "500",
        "unit": "mg"
    }}}


class MedicineCompositionUpdateRequest(BaseUpdateRequest):
    """Request model for updating a medicine composition."""
    
    medicine_id: Optional[UUID] = Field(None, description="Medicine ID")
    salt_name: Optional[str] = Field(None, max_length=255, description="Salt name")
    strength: Optional[str] = Field(None, max_length=50, description="Strength value")
    unit: Optional[str] = Field(None, max_length=20, description="Unit of measurement")
    is_active: Optional[bool] = Field(None, description="Whether the composition is active")
    
    model_config = {"json_schema_extra": {"example": {
        "salt_name": "Paracetamol",
        "strength": "650",
        "unit": "mg",
        "is_active": True
    }}}


class MedicineCompositionResponse(BaseResponse):
    """Response model for medicine composition."""
    
    id: UUID = Field(..., description="Medicine Composition ID")
    medicine_id: UUID = Field(..., description="Medicine ID")
    salt_name: str = Field(..., description="Salt name")
    strength: str = Field(..., description="Strength value")
    unit: str = Field(..., description="Unit of measurement")
    is_active: bool = Field(..., description="Whether the composition is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "mc1e123-4567-8901-2345-678901234567",
        "medicine_id": "m1e123-4567-8901-2345-678901234567",
        "salt_name": "Paracetamol",
        "strength": "500",
        "unit": "mg",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class MedicineCompositionListResponse(ListResponse[MedicineCompositionResponse]):
    """Response model for medicine composition list with pagination."""
    pass
