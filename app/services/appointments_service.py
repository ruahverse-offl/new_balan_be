"""
Appointments Service
Business logic layer for appointments
"""

from typing import Optional
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.repositories.appointments_repository import AppointmentsRepository
from app.schemas.appointments_schema import (
    AppointmentCreateRequest,
    AppointmentUpdateRequest,
    AppointmentResponse,
    AppointmentListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.db.models import Doctor

logger = logging.getLogger(__name__)


class AppointmentsService(BaseService):
    """Service for appointments operations."""
    
    def __init__(self, session: AsyncSession):
        repository = AppointmentsRepository(session)
        super().__init__(repository, session)
    
    async def _get_doctor_name(self, doctor_id: Optional[UUID]) -> str:
        """Look up doctor name by id for response enrichment."""
        if not doctor_id:
            return "—"
        stmt = select(Doctor.id, Doctor.name).where(
            Doctor.id == doctor_id,
            Doctor.is_deleted == False
        )
        result = await self.session.execute(stmt)
        row = result.first()
        return (row.name or "—") if row else "—"

    async def create_appointment(
        self,
        data: AppointmentCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> AppointmentResponse:
        """Create a new appointment."""
        logger.info(f"Creating appointment for patient: {data.patient_name}")
        appointment_data = data.model_dump()
        appointment = await self.repository.create(appointment_data, created_by, created_ip)
        appointment_dict = self._model_to_dict(appointment)
        appointment_dict["doctor_name"] = await self._get_doctor_name(appointment.doctor_id)
        return AppointmentResponse(**appointment_dict)
    
    async def get_appointment_by_id(self, appointment_id: UUID) -> Optional[AppointmentResponse]:
        """Get appointment by ID."""
        appointment = await self.repository.get_by_id(appointment_id)
        if not appointment:
            return None
        appointment_dict = self._model_to_dict(appointment)
        return AppointmentResponse(**appointment_dict)
    
    async def get_appointments_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        doctor_id: Optional[UUID] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> AppointmentListResponse:
        """Get list of appointments with pagination, search, and sort."""
        additional_filters = {}
        if doctor_id:
            additional_filters["doctor_id"] = doctor_id
        if status:
            additional_filters["status"] = status
        if user_id:
            additional_filters["created_by"] = user_id
        
        appointments, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional_filters if additional_filters else None
        )
        
        # Filter by date range if provided
        if date_from or date_to:
            filtered = []
            for apt in appointments:
                if date_from and apt.appointment_date < date_from:
                    continue
                if date_to and apt.appointment_date > date_to:
                    continue
                filtered.append(apt)
            appointments = filtered

        doctor_ids = [a.doctor_id for a in appointments if a.doctor_id]
        name_by_doctor_id = {}
        if doctor_ids:
            stmt = select(Doctor.id, Doctor.name).where(
                Doctor.id.in_(doctor_ids),
                Doctor.is_deleted == False
            )
            result = await self.session.execute(stmt)
            for row in result:
                name_by_doctor_id[str(row.id)] = row.name or "—"

        appointment_responses = []
        for a in appointments:
            d = self._model_to_dict(a)
            d["doctor_name"] = name_by_doctor_id.get(str(a.doctor_id), "—")
            appointment_responses.append(AppointmentResponse(**d))
        return AppointmentListResponse(
            items=appointment_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_appointment(
        self,
        appointment_id: UUID,
        data: AppointmentUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[AppointmentResponse]:
        """Update an appointment."""
        logger.info(f"Updating appointment: {appointment_id}")
        appointment_data = data.model_dump(exclude_unset=True)
        appointment = await self.repository.update(appointment_id, appointment_data, updated_by, updated_ip)
        if not appointment:
            return None
        appointment_dict = self._model_to_dict(appointment)
        appointment_dict["doctor_name"] = await self._get_doctor_name(appointment.doctor_id)
        return AppointmentResponse(**appointment_dict)
    
    async def delete_appointment(
        self,
        appointment_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete an appointment."""
        logger.info(f"Deleting appointment: {appointment_id}")
        return await self.repository.soft_delete(appointment_id, updated_by, updated_ip)
