"""
Doctors Service
Business logic layer for doctors
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.doctors_repository import DoctorsRepository
from app.schemas.doctors_schema import (
    DoctorCreateRequest,
    DoctorUpdateRequest,
    DoctorResponse,
    DoctorListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class DoctorsService(BaseService):
    """Service for doctors operations."""
    
    def __init__(self, session: AsyncSession):
        repository = DoctorsRepository(session)
        super().__init__(repository, session)
    
    async def create_doctor(
        self,
        data: DoctorCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> DoctorResponse:
        """Create a new doctor."""
        logger.info(f"Creating doctor: {data.name}")
        doctor_data = data.model_dump()
        doctor_data["is_active"] = True
        doctor = await self.repository.create(doctor_data, created_by, created_ip)
        doctor_dict = self._model_to_dict(doctor)
        return DoctorResponse(**doctor_dict)
    
    async def get_doctor_by_id(self, doctor_id: UUID) -> Optional[DoctorResponse]:
        """Get doctor by ID."""
        doctor = await self.repository.get_by_id(doctor_id)
        if not doctor:
            return None
        doctor_dict = self._model_to_dict(doctor)
        return DoctorResponse(**doctor_dict)
    
    async def get_doctors_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> DoctorListResponse:
        """Get list of doctors with pagination, search, and sort."""
        doctors, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters={"is_active": is_active} if is_active is not None else None
        )
        doctor_responses = [
            DoctorResponse(**self._model_to_dict(d)) for d in doctors
        ]
        return DoctorListResponse(
            items=doctor_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_doctor(
        self,
        doctor_id: UUID,
        data: DoctorUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[DoctorResponse]:
        """Update a doctor."""
        logger.info(f"Updating doctor: {doctor_id}")
        doctor_data = data.model_dump(exclude_unset=True)
        logger.info(f"Doctor update payload keys: {list(doctor_data.keys())}, name present: {'name' in doctor_data}")
        doctor = await self.repository.update(doctor_id, doctor_data, updated_by, updated_ip)
        if not doctor:
            return None
        doctor_dict = self._model_to_dict(doctor)
        return DoctorResponse(**doctor_dict)
    
    async def delete_doctor(
        self,
        doctor_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a doctor."""
        logger.info(f"Deleting doctor: {doctor_id}")
        return await self.repository.soft_delete(doctor_id, updated_by, updated_ip)
