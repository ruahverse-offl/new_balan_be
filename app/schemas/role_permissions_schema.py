"""
Role Permissions Schema
Pydantic models for role_permissions resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class RolePermissionCreateRequest(BaseCreateRequest):
    """Request model for creating a role permission."""
    
    role_id: UUID = Field(..., description="Role ID")
    permission_id: UUID = Field(..., description="Permission ID")
    # is_active is automatically set to True by the backend
    
    model_config = {"json_schema_extra": {"example": {
        "role_id": "b1f9e123-4567-8901-2345-678901234567",
        "permission_id": "p9x3e123-4567-8901-2345-678901234567"
    }}}


class RolePermissionUpdateRequest(BaseUpdateRequest):
    """Request model for updating a role permission."""
    
    role_id: Optional[UUID] = Field(None, description="Role ID")
    permission_id: Optional[UUID] = Field(None, description="Permission ID")
    is_active: Optional[bool] = Field(None, description="Whether the role permission is active")
    
    model_config = {"json_schema_extra": {"example": {
        "role_id": "b1f9e123-4567-8901-2345-678901234567",
        "permission_id": "p9x3e123-4567-8901-2345-678901234567",
        "is_active": False
    }}}


class RolePermissionResponse(BaseResponse):
    """Response model for role permission."""
    
    id: UUID = Field(..., description="Role Permission ID")
    role_id: UUID = Field(..., description="Role ID")
    permission_id: UUID = Field(..., description="Permission ID")
    is_active: bool = Field(..., description="Whether the role permission is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "rp1e123-4567-8901-2345-678901234567",
        "role_id": "b1f9e123-4567-8901-2345-678901234567",
        "permission_id": "p9x3e123-4567-8901-2345-678901234567",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class RolePermissionListResponse(ListResponse[RolePermissionResponse]):
    """Response model for role permission list with pagination."""
    pass
