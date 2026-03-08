"""
Addresses Schema
Pydantic models for addresses resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import BaseCreateRequest, BaseUpdateRequest, BaseResponse


class AddressCreateRequest(BaseCreateRequest):
    """Request model for creating an address."""

    label: Optional[str] = Field(None, max_length=50, description="Address label (Home, Office, etc.)")
    street: str = Field(..., description="Street address")
    city: str = Field(..., max_length=100, description="City")
    state: str = Field(..., max_length=100, description="State")
    pincode: str = Field(..., max_length=10, description="PIN code")
    country: str = Field(default="India", max_length=100, description="Country")
    is_default: bool = Field(default=False, description="Set as default address")


class AddressUpdateRequest(BaseUpdateRequest):
    """Request model for updating an address."""

    label: Optional[str] = Field(None, max_length=50, description="Address label")
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    pincode: Optional[str] = Field(None, max_length=10, description="PIN code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    is_default: Optional[bool] = Field(None, description="Set as default address")


class AddressResponse(BaseResponse):
    """Response model for address."""

    id: UUID = Field(..., description="Address ID")
    user_id: UUID = Field(..., description="Owner user ID")
    label: Optional[str] = Field(None, description="Address label")
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    pincode: str = Field(..., description="PIN code")
    country: str = Field(..., description="Country")
    is_default: bool = Field(..., description="Whether this is the default address")
    is_active: bool = Field(..., description="Whether the address is active")
