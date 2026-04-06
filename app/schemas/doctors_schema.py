"""
Doctors Schema
Pydantic models for doctors resource
"""

import re
from typing import Optional
from pydantic import EmailStr, Field, field_validator, model_validator
from datetime import datetime, time
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse

_IN_MOBILE_RE = re.compile(r"^[6-9]\d{9}$")


def _normalize_in_phone_value(v: Optional[str]) -> Optional[str]:
    if v is None or not str(v).strip():
        return None
    s = re.sub(r"[\s\-]", "", str(v).strip())
    if s.startswith("+91"):
        s = s[3:]
    if s.startswith("91") and len(s) == 12:
        s = s[2:]
    if s.startswith("0") and len(s) == 11:
        s = s[1:]
    if not _IN_MOBILE_RE.fullmatch(s):
        raise ValueError(
            "Phone must be a 10-digit Indian mobile (starting with 6–9), or empty"
        )
    return s


def _validate_time_pairs(
    morning_start: Optional[time],
    morning_end: Optional[time],
    evening_start: Optional[time],
    evening_end: Optional[time],
) -> None:
    def pair(ms: Optional[time], me: Optional[time], label: str) -> None:
        if ms is None and me is None:
            return
        if ms is None or me is None:
            raise ValueError(f"{label}: provide both start and end times, or neither")
        if ms >= me:
            raise ValueError(f"{label}: end time must be after start time")

    pair(morning_start, morning_end, "Morning hours")
    pair(evening_start, evening_end, "Evening hours")


class DoctorCreateRequest(BaseCreateRequest):
    """Request model for creating a doctor."""
    
    name: str = Field(..., max_length=255, description="Doctor name")
    specialty: str = Field(..., max_length=255, description="Doctor specialty")
    qualifications: Optional[str] = Field(None, description="Doctor qualifications")
    sub_specialty: Optional[str] = Field(None, max_length=255, description="Sub-specialty")
    bio: Optional[str] = Field(None, description="Biography / about")
    experience: Optional[str] = Field(None, description="Experience summary")
    education: Optional[str] = Field(None, description="Education (text or JSON string)")
    specializations: Optional[str] = Field(None, description="Specializations (text or JSON string)")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    email: Optional[EmailStr] = Field(None, max_length=255, description="Email")
    address: Optional[str] = Field(None, description="Address")
    morning_start: Optional[time] = Field(None, description="Morning window start (TIME)")
    morning_end: Optional[time] = Field(None, description="Morning window end (TIME)")
    evening_start: Optional[time] = Field(None, description="Evening window start (TIME)")
    evening_end: Optional[time] = Field(None, description="Evening window end (TIME)")
    morning_timings: Optional[str] = Field(None, max_length=100, description="Morning timings (legacy display text)")
    evening_timings: Optional[str] = Field(None, max_length=100, description="Evening timings (legacy display text)")
    image_url: Optional[str] = Field(None, description="Doctor image URL")
    consultation_fee: Optional[Decimal] = Field(None, ge=0, description="Consultation fee")

    @field_validator("email", mode="before")
    @classmethod
    def email_blank_to_none(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def phone_normalize(cls, v):
        if v is None or (isinstance(v, str) and not str(v).strip()):
            return None
        return _normalize_in_phone_value(str(v))

    @model_validator(mode="after")
    def consultation_slot_times(self):
        _validate_time_pairs(
            self.morning_start,
            self.morning_end,
            self.evening_start,
            self.evening_end,
        )
        return self

    model_config = {"json_schema_extra": {"example": {
        "name": "Dr. M. Sridharan",
        "specialty": "General Physician",
        "qualifications": "MBBS, MD",
        "sub_specialty": "Diabetes",
        "bio": "Senior consultant.",
        "experience": "15+ years",
        "education": "MBBS, MD (General Medicine)",
        "specializations": "Diabetes, Hypertension",
        "phone": "9876543210",
        "email": "dr.sridharan@example.com",
        "address": "Chennai",
        "morning_start": "10:00:00",
        "morning_end": "13:00:00",
        "evening_start": "17:00:00",
        "evening_end": "21:00:00",
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
    sub_specialty: Optional[str] = Field(None, max_length=255, description="Sub-specialty")
    bio: Optional[str] = Field(None, description="Biography / about")
    experience: Optional[str] = Field(None, description="Experience summary")
    education: Optional[str] = Field(None, description="Education (text or JSON string)")
    specializations: Optional[str] = Field(None, description="Specializations (text or JSON string)")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    email: Optional[EmailStr] = Field(None, max_length=255, description="Email")
    address: Optional[str] = Field(None, description="Address")
    morning_start: Optional[time] = Field(None, description="Morning window start (TIME)")
    morning_end: Optional[time] = Field(None, description="Morning window end (TIME)")
    evening_start: Optional[time] = Field(None, description="Evening window start (TIME)")
    evening_end: Optional[time] = Field(None, description="Evening window end (TIME)")
    morning_timings: Optional[str] = Field(None, max_length=100, description="Morning timings (legacy display text)")
    evening_timings: Optional[str] = Field(None, max_length=100, description="Evening timings (legacy display text)")
    image_url: Optional[str] = Field(None, description="Doctor image URL")
    consultation_fee: Optional[Decimal] = Field(None, ge=0, description="Consultation fee")
    is_active: Optional[bool] = Field(None, description="Whether the doctor is active")

    @field_validator("email", mode="before")
    @classmethod
    def email_blank_to_none_update(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def phone_normalize_update(cls, v):
        if v is None or (isinstance(v, str) and not str(v).strip()):
            return None
        return _normalize_in_phone_value(str(v))

    @model_validator(mode="after")
    def consultation_slot_times_update(self):
        _validate_time_pairs(
            self.morning_start,
            self.morning_end,
            self.evening_start,
            self.evening_end,
        )
        return self

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
    sub_specialty: Optional[str] = Field(None, description="Sub-specialty")
    bio: Optional[str] = Field(None, description="Biography / about")
    experience: Optional[str] = Field(None, description="Experience summary")
    education: Optional[str] = Field(None, description="Education (text or JSON string)")
    specializations: Optional[str] = Field(None, description="Specializations (text or JSON string)")
    phone: Optional[str] = Field(None, description="Contact phone")
    email: Optional[str] = Field(None, description="Email")
    address: Optional[str] = Field(None, description="Address")
    morning_start: Optional[time] = Field(None, description="Morning window start (TIME)")
    morning_end: Optional[time] = Field(None, description="Morning window end (TIME)")
    evening_start: Optional[time] = Field(None, description="Evening window start (TIME)")
    evening_end: Optional[time] = Field(None, description="Evening window end (TIME)")
    morning_timings: Optional[str] = Field(None, description="Morning timings (legacy display text)")
    evening_timings: Optional[str] = Field(None, description="Evening timings (legacy display text)")
    image_url: Optional[str] = Field(None, description="Doctor image URL")
    consultation_fee: Optional[Decimal] = Field(None, description="Consultation fee")
    is_active: bool = Field(..., description="Whether the doctor is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "doc1e123-4567-8901-2345-678901234567",
        "name": "Dr. M. Sridharan",
        "specialty": "General Physician",
        "qualifications": "MBBS, MD",
        "sub_specialty": "Diabetes",
        "bio": "Senior consultant.",
        "experience": "15+ years",
        "education": "MBBS, MD",
        "specializations": "Diabetes, Hypertension",
        "phone": "9876543210",
        "email": "dr.sridharan@example.com",
        "address": "Chennai",
        "morning_start": "10:00:00",
        "morning_end": "13:00:00",
        "evening_start": "17:00:00",
        "evening_end": "21:00:00",
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
