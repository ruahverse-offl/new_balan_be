"""
Insurance Enquiries Schema
Pydantic models for insurance_enquiries resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class InsuranceEnquiryCreateRequest(BaseCreateRequest):
    """Request model for creating an insurance enquiry."""

    customer_name: str = Field(..., max_length=255, description="Customer name")
    customer_phone: str = Field(..., max_length=15, description="Customer phone number")
    customer_age: Optional[int] = Field(None, ge=0, le=150, description="Customer age")
    family_size: Optional[int] = Field(None, ge=1, le=20, description="Family size")
    plan_type: Optional[str] = Field(None, max_length=100, description="Preferred plan type")
    message: Optional[str] = Field(None, description="Message from customer")
    status: str = Field("PENDING", max_length=50, description="Enquiry status")

    model_config = {"json_schema_extra": {"example": {
        "customer_name": "Ramesh Kumar",
        "customer_phone": "9876543210",
        "customer_age": 35,
        "family_size": 4,
        "plan_type": "Family Plan",
        "message": "Looking for family health insurance with maternity cover",
        "status": "PENDING"
    }}}


class InsuranceEnquiryUpdateRequest(BaseUpdateRequest):
    """Request model for updating an insurance enquiry."""

    customer_name: Optional[str] = Field(None, max_length=255, description="Customer name")
    customer_phone: Optional[str] = Field(None, max_length=15, description="Customer phone number")
    customer_age: Optional[int] = Field(None, ge=0, le=150, description="Customer age")
    family_size: Optional[int] = Field(None, ge=1, le=20, description="Family size")
    plan_type: Optional[str] = Field(None, max_length=100, description="Preferred plan type")
    message: Optional[str] = Field(None, description="Message from customer")
    status: Optional[str] = Field(None, max_length=50, description="Enquiry status")
    admin_notes: Optional[str] = Field(None, description="Admin notes")

    model_config = {"json_schema_extra": {"example": {
        "status": "CONTACTED",
        "admin_notes": "Called customer, meeting scheduled for Friday"
    }}}


class InsuranceEnquiryResponse(BaseResponse):
    """Response model for insurance enquiry."""

    id: UUID = Field(..., description="Enquiry ID")
    customer_name: str = Field(..., description="Customer name")
    customer_phone: str = Field(..., description="Customer phone number")
    customer_age: Optional[int] = Field(None, description="Customer age")
    family_size: Optional[int] = Field(None, description="Family size")
    plan_type: Optional[str] = Field(None, description="Preferred plan type")
    message: Optional[str] = Field(None, description="Message from customer")
    status: str = Field(..., description="Enquiry status")
    admin_notes: Optional[str] = Field(None, description="Admin notes")

    model_config = {"json_schema_extra": {"example": {
        "id": "ie1e123-4567-8901-2345-678901234567",
        "customer_name": "Ramesh Kumar",
        "customer_phone": "9876543210",
        "customer_age": 35,
        "family_size": 4,
        "plan_type": "Family Plan",
        "message": "Looking for family health insurance",
        "status": "PENDING",
        "admin_notes": None,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class InsuranceEnquiryListResponse(ListResponse[InsuranceEnquiryResponse]):
    """Response model for insurance enquiry list with pagination."""
    pass
