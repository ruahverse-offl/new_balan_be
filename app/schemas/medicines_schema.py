"""
Medicines Schema
Pydantic models for medicines resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class MedicineCreateRequest(BaseCreateRequest):
    """Request model for creating a medicine."""
    
    name: str = Field(..., max_length=255, description="Medicine name")
    dosage_form: str = Field(..., max_length=100, description="Dosage form")
    therapeutic_category_id: UUID = Field(..., description="Therapeutic category ID")
    is_prescription_required: bool = Field(False, description="Whether prescription is required")
    is_controlled: bool = Field(False, description="Whether the medicine is controlled")
    schedule_type: str = Field(..., max_length=10, description="Schedule type (e.g., OTC)")
    description: Optional[str] = Field(None, description="Medicine description")
    is_available: Optional[bool] = Field(True, description="Available for sale (default True)")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "Paracetamol",
        "dosage_form": "Tablet",
        "therapeutic_category_id": "tc1e123-4567-8901-2345-678901234567",
        "is_prescription_required": False,
        "is_controlled": False,
        "schedule_type": "OTC",
        "description": "Pain reliever"
    }}}


class MedicineUpdateRequest(BaseUpdateRequest):
    """Request model for updating a medicine."""
    
    name: Optional[str] = Field(None, max_length=255, description="Medicine name")
    dosage_form: Optional[str] = Field(None, max_length=100, description="Dosage form")
    therapeutic_category_id: Optional[UUID] = Field(None, description="Therapeutic category ID")
    is_prescription_required: Optional[bool] = Field(None, description="Whether prescription is required")
    is_controlled: Optional[bool] = Field(None, description="Whether the medicine is controlled")
    schedule_type: Optional[str] = Field(None, max_length=10, description="Schedule type")
    description: Optional[str] = Field(None, description="Medicine description")
    is_active: Optional[bool] = Field(None, description="Whether the medicine is active")
    is_available: Optional[bool] = Field(None, description="Available for sale; if False, all brands become unavailable")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "Paracetamol 500mg",
        "dosage_form": "Tablet",
        "is_prescription_required": True,
        "is_active": True
    }}}


class MedicineResponse(BaseResponse):
    """Response model for medicine."""
    
    id: UUID = Field(..., description="Medicine ID")
    name: str = Field(..., description="Medicine name")
    dosage_form: str = Field(..., description="Dosage form")
    therapeutic_category_id: UUID = Field(..., description="Therapeutic category ID")
    therapeutic_category_name: Optional[str] = Field(None, description="Therapeutic category name (in list responses)")
    is_prescription_required: bool = Field(..., description="Whether prescription is required")
    is_controlled: bool = Field(..., description="Whether the medicine is controlled")
    schedule_type: str = Field(..., description="Schedule type")
    description: Optional[str] = Field(None, description="Medicine description")
    is_active: bool = Field(..., description="Whether the medicine is active")
    is_available: bool = Field(True, description="Available for sale; when False, all its brands are unavailable")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "m1e123-4567-8901-2345-678901234567",
        "name": "Paracetamol",
        "dosage_form": "Tablet",
        "therapeutic_category_id": "tc1e123-4567-8901-2345-678901234567",
        "is_prescription_required": False,
        "is_controlled": False,
        "schedule_type": "OTC",
        "description": "Pain reliever",
        "is_active": True,
        "is_available": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class MedicineListResponse(ListResponse[MedicineResponse]):
    """Response model for medicine list with pagination."""
    pass
