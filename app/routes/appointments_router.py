"""
Appointments Router
FastAPI routes for appointments resource
"""

from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.appointments_service import AppointmentsService
from app.schemas.appointments_schema import (
    AppointmentCreateRequest,
    AppointmentUpdateRequest,
    AppointmentResponse,
    AppointmentListResponse
)
from app.utils.auth import get_current_user_id_optional
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AppointmentResponse)
async def create_appointment(
    data: AppointmentCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Create a new appointment."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = AppointmentsService(db)
    appointment = await service.create_appointment(data, user_id, ip_address)
    await db.commit()
    return appointment


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment_by_id(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Get appointment by ID."""
    service = AppointmentsService(db)
    appointment = await service.get_appointment_by_id(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointment_id} not found"
        )
    # Check if user owns the appointment or has APPOINTMENT_VIEW permission
    if current_user_id:
        from app.utils.rbac import RBACService
        rbac_service = RBACService(db)
        has_permission = await rbac_service.has_permission(current_user_id, "APPOINTMENT_VIEW")
        if not has_permission and str(appointment.created_by) != str(current_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own appointments"
            )
    return appointment


@router.get("/", response_model=AppointmentListResponse)
async def get_appointments_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    doctor_id: Optional[UUID] = Query(default=None),
    status: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """
    Get list of appointments.

    Users with APPOINTMENT_VIEW permission can see all appointments.
    Users without it can only see their own appointments (filtered by created_by).
    """
    user_id_filter = None
    if current_user_id:
        from app.utils.rbac import RBACService
        rbac_service = RBACService(db)
        has_permission = await rbac_service.has_permission(current_user_id, "APPOINTMENT_VIEW")
        if not has_permission:
            user_id_filter = current_user_id

    service = AppointmentsService(db)
    result = await service.get_appointments_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        doctor_id=doctor_id, status=status, date_from=date_from, date_to=date_to,
        user_id=user_id_filter
    )
    return result


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Update an appointment."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = AppointmentsService(db)
    appointment = await service.update_appointment(appointment_id, data, user_id, ip_address)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointment_id} not found"
        )
    await db.commit()
    return appointment


@router.delete("/{appointment_id}", status_code=status.HTTP_200_OK)
async def delete_appointment(
    appointment_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Soft delete an appointment."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = AppointmentsService(db)
    deleted = await service.delete_appointment(appointment_id, user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointment_id} not found"
        )
    return {"message": "Appointment deleted successfully", "id": str(appointment_id)}
