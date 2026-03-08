"""
Roles Schema
Pydantic models for roles resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class RoleCreateRequest(BaseCreateRequest):
    """Request model for creating a role."""
    
    name: str = Field(..., max_length=100, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    # is_active is automatically set to True by the backend
    
    model_config = {"json_schema_extra": {"example": {
        "name": "PHARMACIST",
        "description": "Licensed pharmacist role"
    }}}


class RoleUpdateRequest(BaseUpdateRequest):
    """Request model for updating a role."""
    
    name: Optional[str] = Field(None, max_length=100, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    is_active: Optional[bool] = Field(None, description="Whether the role is active")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "SENIOR_PHARMACIST",
        "description": "Senior licensed pharmacist role",
        "is_active": True
    }}}


class RoleResponse(BaseResponse):
    """Response model for role."""
    
    id: UUID = Field(..., description="Role ID")
    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    is_active: bool = Field(..., description="Whether the role is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "b1f9e123-4567-8901-2345-678901234567",
        "name": "PHARMACIST",
        "description": "Licensed pharmacist role",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class RoleListResponse(ListResponse[RoleResponse]):
    """Response model for role list with pagination."""
    pass
