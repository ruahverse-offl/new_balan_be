"""
Therapeutic Categories Schema
Pydantic models for therapeutic_categories resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class TherapeuticCategoryCreateRequest(BaseCreateRequest):
    """Request model for creating a therapeutic category."""
    
    name: str = Field(..., max_length=255, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    # is_active is automatically set to True by the backend
    
    model_config = {"json_schema_extra": {"example": {
        "name": "Antibiotic",
        "description": "Drugs used to treat infections"
    }}}


class TherapeuticCategoryUpdateRequest(BaseUpdateRequest):
    """Request model for updating a therapeutic category."""
    
    name: Optional[str] = Field(None, max_length=255, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: Optional[bool] = Field(None, description="Whether the category is active")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "Antibiotic - Broad Spectrum",
        "description": "Broad spectrum antibiotics for infections",
        "is_active": True
    }}}


class TherapeuticCategoryResponse(BaseResponse):
    """Response model for therapeutic category."""
    
    id: UUID = Field(..., description="Therapeutic Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: bool = Field(..., description="Whether the category is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "tc1e123-4567-8901-2345-678901234567",
        "name": "Antibiotic",
        "description": "Drugs used to treat infections",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class TherapeuticCategoryListResponse(ListResponse[TherapeuticCategoryResponse]):
    """Response model for therapeutic category list with pagination."""
    pass
