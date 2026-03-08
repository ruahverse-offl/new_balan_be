"""
Doctors Schema
Pydantic models for doctors resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class DoctorCreateRequest(BaseCreateRequest):
    """Request model for creating a doctor."""
    
    name: str = Field(..., max_length=255, description="Doctor name")
    specialty: str = Field(..., max_length=255, description="Doctor specialty")
    qualifications: Optional[str] = Field(None, description="Doctor qualifications")
    morning_timings: Optional[str] = Field(None, max_length=100, description="Morning timings")
    evening_timings: Optional[str] = Field(None, max_length=100, description="Evening timings")
    image_url: Optional[str] = Field(None, description="Doctor image URL")
    consultation_fee: Optional[Decimal] = Field(None, description="Consultation fee")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "Dr. M. Sridharan",
        "specialty": "General Physician",
        "qualifications": "MBBS, MD",
        "morning_timings": "10:00 AM - 1:00 PM",
        "evening_timings": "5:00 PM - 9:00 PM",
        "image_url": "https://example.com/doctor.jpg",
        "consultation_fee": 500.00
    }}}


class DoctorUpdateRequest(BaseUpdateRequest):
    """Request model for updating a doctor."""
    
    name: Optional[str] = Field(None, max_length=255, description="Doctor name")
    specialty: Optional[str] = Field(None, max_length=255, description="Doctor specialty")
    qualifications: Optional[str] = Field(None, description="Doctor qualifications")
    morning_timings: Optional[str] = Field(None, max_length=100, description="Morning timings")
    evening_timings: Optional[str] = Field(None, max_length=100, description="Evening timings")
    image_url: Optional[str] = Field(None, description="Doctor image URL")
    consultation_fee: Optional[Decimal] = Field(None, description="Consultation fee")
    is_active: Optional[bool] = Field(None, description="Whether the doctor is active")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "Dr. M. Sridharan",
        "specialty": "General Physician",
        "is_active": True
    }}}


class DoctorResponse(BaseResponse):
    """Response model for doctor."""
    
    id: UUID = Field(..., description="Doctor ID")
    name: str = Field(..., description="Doctor name")
    specialty: str = Field(..., description="Doctor specialty")
    qualifications: Optional[str] = Field(None, description="Doctor qualifications")
    morning_timings: Optional[str] = Field(None, description="Morning timings")
    evening_timings: Optional[str] = Field(None, description="Evening timings")
    image_url: Optional[str] = Field(None, description="Doctor image URL")
    consultation_fee: Optional[Decimal] = Field(None, description="Consultation fee")
    is_active: bool = Field(..., description="Whether the doctor is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "doc1e123-4567-8901-2345-678901234567",
        "name": "Dr. M. Sridharan",
        "specialty": "General Physician",
        "qualifications": "MBBS, MD",
        "morning_timings": "10:00 AM - 1:00 PM",
        "evening_timings": "5:00 PM - 9:00 PM",
        "image_url": "https://example.com/doctor.jpg",
        "consultation_fee": 500.00,
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class DoctorListResponse(ListResponse[DoctorResponse]):
    """Response model for doctor list with pagination."""
    pass
