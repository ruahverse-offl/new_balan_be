"""
Polyclinic Tests Schema
Pydantic models for polyclinic_tests resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class PolyclinicTestCreateRequest(BaseCreateRequest):
    """Request model for creating a polyclinic test."""
    
    name: str = Field(..., max_length=255, description="Test name")
    description: Optional[str] = Field(None, description="Test description")
    price: Decimal = Field(..., description="Test price")
    duration: Optional[str] = Field(None, max_length=50, description="Test duration")
    fasting_required: bool = Field(False, description="Whether fasting is required")
    icon_name: Optional[str] = Field(None, max_length=100, description="Icon name for frontend")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "Blood Test",
        "description": "Complete blood count (CBC), hemoglobin, and comprehensive blood analysis.",
        "price": 300.00,
        "duration": "15-20 mins",
        "fasting_required": False,
        "icon_name": "TestTube"
    }}}


class PolyclinicTestUpdateRequest(BaseUpdateRequest):
    """Request model for updating a polyclinic test."""
    
    name: Optional[str] = Field(None, max_length=255, description="Test name")
    description: Optional[str] = Field(None, description="Test description")
    price: Optional[Decimal] = Field(None, description="Test price")
    duration: Optional[str] = Field(None, max_length=50, description="Test duration")
    fasting_required: Optional[bool] = Field(None, description="Whether fasting is required")
    icon_name: Optional[str] = Field(None, max_length=100, description="Icon name for frontend")
    is_active: Optional[bool] = Field(None, description="Whether the test is active")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "Blood Test",
        "price": 350.00,
        "is_active": True
    }}}


class PolyclinicTestResponse(BaseResponse):
    """Response model for polyclinic test."""
    
    id: UUID = Field(..., description="Test ID")
    name: str = Field(..., description="Test name")
    description: Optional[str] = Field(None, description="Test description")
    price: Decimal = Field(..., description="Test price")
    duration: Optional[str] = Field(None, description="Test duration")
    fasting_required: bool = Field(..., description="Whether fasting is required")
    icon_name: Optional[str] = Field(None, description="Icon name for frontend")
    is_active: bool = Field(..., description="Whether the test is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "pt1e123-4567-8901-2345-678901234567",
        "name": "Blood Test",
        "description": "Complete blood count (CBC), hemoglobin, and comprehensive blood analysis.",
        "price": 300.00,
        "duration": "15-20 mins",
        "fasting_required": False,
        "icon_name": "TestTube",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class PolyclinicTestListResponse(ListResponse[PolyclinicTestResponse]):
    """Response model for polyclinic test list with pagination."""
    pass
