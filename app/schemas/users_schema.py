"""
Users Schema
Pydantic models for users resource
"""

from typing import Optional
from pydantic import Field, EmailStr
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class UserCreateRequest(BaseCreateRequest):
    """Request model for creating a user."""
    
    role_id: UUID = Field(..., description="Role ID - staff get all permissions of this role")
    full_name: str = Field(..., max_length=255, description="User's full name")
    mobile_number: str = Field(..., max_length=15, description="Mobile number")
    email: EmailStr = Field(..., description="Email address")
    password: Optional[str] = Field(None, description="Plain password (hashed by backend); required if password_hash not set")
    password_hash: Optional[str] = Field(None, description="Pre-hashed password (optional; if password is sent it is hashed instead)")
    # is_active is automatically set to True by the backend
    
    model_config = {"json_schema_extra": {"example": {
        "role_id": "b1f9e123-4567-8901-2345-678901234567",
        "full_name": "Rahul Sharma",
        "mobile_number": "9876543210",
        "email": "rahul@gmail.com",
        "password": "secret123"
    }}}


class UserUpdateRequest(BaseUpdateRequest):
    """Request model for updating a user."""
    
    role_id: Optional[UUID] = Field(None, description="Role ID")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    mobile_number: Optional[str] = Field(None, max_length=15, description="Mobile number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    password: Optional[str] = Field(None, description="New plain password (hashed by backend)")
    password_hash: Optional[str] = Field(None, description="Pre-hashed password")
    is_active: Optional[bool] = Field(None, description="Whether the user is active")
    
    model_config = {"json_schema_extra": {"example": {
        "role_id": "b1f9e123-4567-8901-2345-678901234567",
        "full_name": "Rahul Kumar Sharma",
        "mobile_number": "9876543211",
        "email": "rahul.kumar@gmail.com",
        "is_active": True
    }}}


class UserResponse(BaseResponse):
    """Response model for user."""

    id: UUID = Field(..., description="User ID")
    role_id: UUID = Field(..., description="Role ID")
    full_name: str = Field(..., description="User's full name")
    mobile_number: str = Field(..., description="Mobile number")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(..., description="Whether the user is active")

    model_config = {"from_attributes": True, "json_schema_extra": {"example": {
        "id": "u123e456-7890-1234-5678-901234567890",
        "role_id": "b1f9e123-4567-8901-2345-678901234567",
        "full_name": "Rahul Sharma",
        "mobile_number": "9876543210",
        "email": "rahul@gmail.com",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class UserListResponse(ListResponse[UserResponse]):
    """Response model for user list with pagination."""
    pass
