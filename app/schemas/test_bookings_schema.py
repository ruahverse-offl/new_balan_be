"""
Test Bookings Schema
Pydantic models for test_bookings resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime, date
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class TestBookingCreateRequest(BaseCreateRequest):
    """Request model for creating a test booking."""
    
    test_id: UUID = Field(..., description="Test ID")
    patient_name: str = Field(..., max_length=255, description="Patient name")
    patient_phone: str = Field(..., max_length=15, description="Patient phone number")
    booking_date: date = Field(..., description="Booking date")
    booking_time: Optional[str] = Field(None, max_length=50, description="Booking time")
    status: str = Field("PENDING", max_length=50, description="Booking status")
    notes: Optional[str] = Field(None, description="Admin notes")
    
    model_config = {"json_schema_extra": {"example": {
        "test_id": "pt1e123-4567-8901-2345-678901234567",
        "patient_name": "Lakshmi Menon",
        "patient_phone": "9876543302",
        "booking_date": "2026-02-16",
        "booking_time": "11:00 AM",
        "status": "PENDING",
        "notes": "Patient called at 3 PM, needs fasting test"
    }}}


class TestBookingUpdateRequest(BaseUpdateRequest):
    """Request model for updating a test booking."""
    
    test_id: Optional[UUID] = Field(None, description="Test ID")
    patient_name: Optional[str] = Field(None, max_length=255, description="Patient name")
    patient_phone: Optional[str] = Field(None, max_length=15, description="Patient phone number")
    booking_date: Optional[date] = Field(None, description="Booking date")
    booking_time: Optional[str] = Field(None, max_length=50, description="Booking time")
    status: Optional[str] = Field(None, max_length=50, description="Booking status")
    notes: Optional[str] = Field(None, description="Admin notes")
    
    model_config = {"json_schema_extra": {"example": {
        "status": "CONFIRMED",
        "notes": "Confirmed booking"
    }}}


class TestBookingResponse(BaseResponse):
    """Response model for test booking."""
    
    id: UUID = Field(..., description="Test booking ID")
    test_id: UUID = Field(..., description="Test ID")
    test_name: Optional[str] = Field(None, description="Test name (included in list responses)")
    patient_name: str = Field(..., description="Patient name")
    patient_phone: str = Field(..., description="Patient phone number")
    booking_date: date = Field(..., description="Booking date")
    booking_time: Optional[str] = Field(None, description="Booking time")
    status: str = Field(..., description="Booking status")
    notes: Optional[str] = Field(None, description="Admin notes")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "tb1e123-4567-8901-2345-678901234567",
        "test_id": "pt1e123-4567-8901-2345-678901234567",
        "patient_name": "Lakshmi Menon",
        "patient_phone": "9876543302",
        "booking_date": "2026-02-16",
        "booking_time": "11:00 AM",
        "status": "PENDING",
        "notes": "Patient called at 3 PM, needs fasting test",
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class TestBookingListResponse(ListResponse[TestBookingResponse]):
    """Response model for test booking list with pagination."""
    pass
