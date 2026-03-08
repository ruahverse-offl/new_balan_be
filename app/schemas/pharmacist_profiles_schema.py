"""
Pharmacist Profiles Schema
Pydantic models for pharmacist_profiles resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime, date
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class PharmacistProfileCreateRequest(BaseCreateRequest):
    """Request model for creating a pharmacist profile."""
    
    user_id: UUID = Field(..., description="User ID")
    license_number: str = Field(..., max_length=100, description="License number")
    license_valid_till: date = Field(..., description="License validity date")
    # is_active is automatically set to True by the backend
    
    model_config = {"json_schema_extra": {"example": {
        "user_id": "u123e456-7890-1234-5678-901234567890",
        "license_number": "PHARMA-AP-12345",
        "license_valid_till": "2027-12-31"
    }}}


class PharmacistProfileUpdateRequest(BaseUpdateRequest):
    """Request model for updating a pharmacist profile."""
    
    user_id: Optional[UUID] = Field(None, description="User ID")
    license_number: Optional[str] = Field(None, max_length=100, description="License number")
    license_valid_till: Optional[date] = Field(None, description="License validity date")
    is_active: Optional[bool] = Field(None, description="Whether the profile is active")
    
    model_config = {"json_schema_extra": {"example": {
        "license_number": "PHARMA-AP-12346",
        "license_valid_till": "2028-12-31",
        "is_active": True
    }}}


class PharmacistProfileResponse(BaseResponse):
    """Response model for pharmacist profile."""
    
    user_id: UUID = Field(..., description="User ID")
    license_number: str = Field(..., description="License number")
    license_valid_till: date = Field(..., description="License validity date")
    is_active: bool = Field(..., description="Whether the profile is active")
    
    model_config = {"json_schema_extra": {"example": {
        "user_id": "u123e456-7890-1234-5678-901234567890",
        "license_number": "PHARMA-AP-12345",
        "license_valid_till": "2027-12-31",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class PharmacistProfileListResponse(ListResponse[PharmacistProfileResponse]):
    """Response model for pharmacist profile list with pagination."""
    pass
