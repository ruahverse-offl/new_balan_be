"""
Prescriptions Schema
Pydantic models for prescriptions resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class PrescriptionCreateRequest(BaseCreateRequest):
    """Request model for creating a prescription."""

    id: Optional[UUID] = Field(None, description="Prescription ID (optional; for upload flow to use same ID as file reference)")
    customer_id: UUID = Field(..., description="Customer ID")
    order_id: Optional[UUID] = Field(None, description="Order ID (if linked to order)")
    file_url: str = Field(..., description="File storage URL")
    file_name: str = Field(..., max_length=255, description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., max_length=100, description="MIME type")


class PrescriptionUpdateRequest(BaseUpdateRequest):
    """Request model for updating a prescription."""

    order_id: Optional[UUID] = Field(None, description="Link to order (set when order is created)")
    status: Optional[str] = Field(None, max_length=50, description="Status (PENDING, APPROVED, REJECTED)")
    review_notes: Optional[str] = Field(None, description="Review notes")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")


class PrescriptionResponse(BaseResponse):
    """Response model for a prescription."""

    id: UUID = Field(..., description="Prescription ID")
    customer_id: UUID = Field(..., description="Customer ID")
    order_id: Optional[UUID] = Field(None, description="Linked Order ID")
    file_url: str = Field(..., description="File storage URL")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="MIME type")
    status: str = Field(..., description="Status (PENDING, APPROVED, REJECTED)")
    reviewed_by: Optional[UUID] = Field(None, description="Reviewed by user ID")
    review_notes: Optional[str] = Field(None, description="Review notes")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")

    model_config = {"from_attributes": True}


class PrescriptionListResponse(ListResponse[PrescriptionResponse]):
    """List response for prescriptions."""
    pass
