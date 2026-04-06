"""
Appointments Schema
Pydantic models for appointments resource
"""

from typing import Any, Optional
from pydantic import Field, field_validator
from datetime import datetime, date, time
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


def _coerce_appointment_time(v: Any) -> Optional[time]:
    """Parse JSON / form values into datetime.time for DB TIME column."""
    if v is None:
        return None
    if isinstance(v, time):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p", "%I:%M%p", "%I:%M:%S%p"):
            try:
                return datetime.strptime(s, fmt).time()
            except ValueError:
                continue
        try:
            return time.fromisoformat(s)
        except ValueError:
            pass
    raise ValueError("Invalid appointment_time; use HH:MM, HH:MM:SS, or 12-hour with AM/PM")


class AppointmentCreateRequest(BaseCreateRequest):
    """Request model for creating an appointment."""

    doctor_id: UUID = Field(..., description="Doctor ID")
    patient_name: str = Field(..., max_length=255, description="Patient name")
    patient_phone: str = Field(..., max_length=15, description="Patient phone number")
    appointment_date: date = Field(..., description="Appointment date")
    appointment_time: Optional[time] = Field(None, description="Appointment time (TIME; JSON as HH:MM:SS or HH:MM)")
    status: str = Field("PENDING", max_length=50, description="Appointment status")
    message: Optional[str] = Field(None, description="Message from patient")
    notes: Optional[str] = Field(None, description="Admin notes")

    @field_validator("appointment_time", mode="before")
    @classmethod
    def _appointment_time_create(cls, v: Any) -> Optional[time]:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return _coerce_appointment_time(v)

    model_config = {"json_schema_extra": {"example": {
        "doctor_id": "doc1e123-4567-8901-2345-678901234567",
        "patient_name": "Ramesh Iyer",
        "patient_phone": "9876543301",
        "appointment_date": "2026-02-15",
        "appointment_time": "10:00:00",
        "status": "CONFIRMED",
        "message": "Follow-up consultation for fever",
        "notes": "Patient called at 2 PM"
    }}}


class AppointmentUpdateRequest(BaseUpdateRequest):
    """Request model for updating an appointment."""

    doctor_id: Optional[UUID] = Field(None, description="Doctor ID")
    patient_name: Optional[str] = Field(None, max_length=255, description="Patient name")
    patient_phone: Optional[str] = Field(None, max_length=15, description="Patient phone number")
    appointment_date: Optional[date] = Field(None, description="Appointment date")
    appointment_time: Optional[time] = Field(None, description="Appointment time (TIME; JSON as HH:MM:SS or HH:MM)")
    status: Optional[str] = Field(None, max_length=50, description="Appointment status")
    message: Optional[str] = Field(None, description="Message from patient")
    notes: Optional[str] = Field(None, description="Admin notes")

    @field_validator("appointment_time", mode="before")
    @classmethod
    def _appointment_time_update(cls, v: Any) -> Optional[time]:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return _coerce_appointment_time(v)

    model_config = {"json_schema_extra": {"example": {
        "status": "CONFIRMED",
        "notes": "Confirmed appointment"
    }}}


class AppointmentResponse(BaseResponse):
    """Response model for appointment."""

    id: UUID = Field(..., description="Appointment ID")
    doctor_id: Optional[UUID] = Field(None, description="Doctor ID (optional for legacy rows)")
    doctor_name: Optional[str] = Field(None, description="Doctor name (included in list responses)")
    patient_name: str = Field(..., description="Patient name")
    patient_phone: str = Field(..., description="Patient phone number")
    appointment_date: date = Field(..., description="Appointment date")
    appointment_time: Optional[time] = Field(None, description="Appointment time (TIME)")
    status: str = Field(..., description="Appointment status")
    message: Optional[str] = Field(None, description="Message from patient")
    notes: Optional[str] = Field(None, description="Admin notes")

    model_config = {"json_schema_extra": {"example": {
        "id": "apt1e123-4567-8901-2345-678901234567",
        "doctor_id": "doc1e123-4567-8901-2345-678901234567",
        "patient_name": "Ramesh Iyer",
        "patient_phone": "9876543301",
        "appointment_date": "2026-02-15",
        "appointment_time": "10:00:00",
        "status": "CONFIRMED",
        "message": "Follow-up consultation for fever",
        "notes": "Patient called at 2 PM",
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class AppointmentListResponse(ListResponse[AppointmentResponse]):
    """Response model for appointment list with pagination."""
    pass
