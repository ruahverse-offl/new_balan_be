"""
Prescriptions Service
Business logic layer for prescriptions
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.prescriptions_repository import PrescriptionsRepository
from app.schemas.prescriptions_schema import (
    PrescriptionCreateRequest,
    PrescriptionUpdateRequest,
    PrescriptionResponse,
    PrescriptionListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PrescriptionsService(BaseService):
    """Service for prescriptions operations."""

    def __init__(self, session: AsyncSession):
        repository = PrescriptionsRepository(session)
        super().__init__(repository, session)

    async def create_prescription(
        self,
        data: PrescriptionCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> PrescriptionResponse:
        """Create a new prescription."""
        logger.info(f"Creating prescription for customer: {data.customer_id}")
        prescription_data = data.model_dump()
        prescription_data["status"] = "PENDING"
        prescription = await self.repository.create(prescription_data, created_by, created_ip)
        prescription_dict = self._model_to_dict(prescription)
        return PrescriptionResponse(**prescription_dict)

    async def get_prescription_by_id(self, prescription_id: UUID) -> Optional[PrescriptionResponse]:
        """Get prescription by ID."""
        prescription = await self.repository.get_by_id(prescription_id)
        if not prescription:
            return None
        prescription_dict = self._model_to_dict(prescription)
        return PrescriptionResponse(**prescription_dict)

    async def get_prescriptions_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        status: Optional[str] = None
    ) -> PrescriptionListResponse:
        """Get list of prescriptions with pagination, search, and sort."""
        additional_filters = {}
        if status:
            additional_filters["status"] = status
        prescriptions, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional_filters if additional_filters else None
        )
        responses = [
            PrescriptionResponse(**self._model_to_dict(p)) for p in prescriptions
        ]
        return PrescriptionListResponse(
            items=responses,
            pagination=PaginationResponse(**pagination)
        )

    async def approve_prescription(
        self,
        prescription_id: UUID,
        reviewed_by: UUID,
        notes: Optional[str],
        updated_ip: str
    ) -> Optional[PrescriptionResponse]:
        """Approve a prescription."""
        logger.info(f"Approving prescription: {prescription_id}")
        update_data = {
            "status": "APPROVED",
            "reviewed_by": reviewed_by,
            "review_notes": notes
        }
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        prescription = await self.repository.update(prescription_id, update_data, reviewed_by, updated_ip)
        if not prescription:
            return None
        return PrescriptionResponse(**self._model_to_dict(prescription))

    async def reject_prescription(
        self,
        prescription_id: UUID,
        reviewed_by: UUID,
        rejection_reason: str,
        updated_ip: str
    ) -> Optional[PrescriptionResponse]:
        """Reject a prescription."""
        logger.info(f"Rejecting prescription: {prescription_id}")
        update_data = {
            "status": "REJECTED",
            "reviewed_by": reviewed_by,
            "rejection_reason": rejection_reason
        }
        prescription = await self.repository.update(prescription_id, update_data, reviewed_by, updated_ip)
        if not prescription:
            return None
        return PrescriptionResponse(**self._model_to_dict(prescription))

    async def update_prescription(
        self,
        prescription_id: UUID,
        data: PrescriptionUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[PrescriptionResponse]:
        """Update a prescription."""
        logger.info(f"Updating prescription: {prescription_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        prescription = await self.repository.update(prescription_id, update_data, updated_by, updated_ip)
        if not prescription:
            return None
        return PrescriptionResponse(**self._model_to_dict(prescription))

    async def delete_prescription(
        self,
        prescription_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a prescription."""
        logger.info(f"Deleting prescription: {prescription_id}")
        return await self.repository.soft_delete(prescription_id, updated_by, updated_ip)
