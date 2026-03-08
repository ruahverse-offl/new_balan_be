"""
Permissions Schema
Pydantic models for permissions resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class PermissionCreateRequest(BaseCreateRequest):
    """Request model for creating a permission."""
    
    code: str = Field(..., max_length=100, description="Permission code")
    description: Optional[str] = Field(None, description="Permission description")
    # is_active is automatically set to True by the backend
    
    model_config = {"json_schema_extra": {"example": {
        "code": "PRESCRIPTION_REVIEW",
        "description": "Can review prescriptions"
    }}}


class PermissionUpdateRequest(BaseUpdateRequest):
    """Request model for updating a permission."""
    
    code: Optional[str] = Field(None, max_length=100, description="Permission code")
    description: Optional[str] = Field(None, description="Permission description")
    is_active: Optional[bool] = Field(None, description="Whether the permission is active")
    
    model_config = {"json_schema_extra": {"example": {
        "code": "PRESCRIPTION_APPROVE",
        "description": "Can approve prescriptions",
        "is_active": True
    }}}


class PermissionResponse(BaseResponse):
    """Response model for permission."""
    
    id: UUID = Field(..., description="Permission ID")
    code: str = Field(..., description="Permission code")
    description: Optional[str] = Field(None, description="Permission description")
    is_active: bool = Field(..., description="Whether the permission is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "p9x3e123-4567-8901-2345-678901234567",
        "code": "PRESCRIPTION_REVIEW",
        "description": "Can review prescriptions",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class PermissionListResponse(ListResponse[PermissionResponse]):
    """Response model for permission list with pagination."""
    pass
