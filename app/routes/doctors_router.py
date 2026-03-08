"""
Doctors Router
FastAPI routes for doctors resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.doctors_service import DoctorsService
from app.schemas.doctors_schema import (
    DoctorCreateRequest,
    DoctorUpdateRequest,
    DoctorResponse,
    DoctorListResponse
)
from app.utils.auth import get_current_user_id_optional
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/doctors", tags=["doctors"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DoctorResponse)
async def create_doctor(
    data: DoctorCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Create a new doctor."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = DoctorsService(db)
    doctor = await service.create_doctor(data, user_id, ip_address)
    return doctor


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor_by_id(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get doctor by ID."""
    service = DoctorsService(db)
    doctor = await service.get_doctor_by_id(doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {doctor_id} not found"
        )
    return doctor


@router.get("/", response_model=DoctorListResponse)
async def get_doctors_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of doctors with pagination, search, and sort."""
    service = DoctorsService(db)
    result = await service.get_doctors_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        is_active=is_active
    )
    return result


@router.patch("/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: UUID,
    data: DoctorUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Update a doctor."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = DoctorsService(db)
    doctor = await service.update_doctor(doctor_id, data, user_id, ip_address)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {doctor_id} not found"
        )
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_200_OK)
async def delete_doctor(
    doctor_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Soft delete a doctor."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = DoctorsService(db)
    deleted = await service.delete_doctor(doctor_id, user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {doctor_id} not found"
        )
    return {"message": "Doctor deleted successfully", "id": str(doctor_id)}
