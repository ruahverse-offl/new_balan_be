"""
Insurance Enquiries Service
Business logic layer for insurance_enquiries
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.insurance_enquiries_repository import InsuranceEnquiriesRepository
from app.schemas.insurance_enquiries_schema import (
    InsuranceEnquiryCreateRequest,
    InsuranceEnquiryUpdateRequest,
    InsuranceEnquiryResponse,
    InsuranceEnquiryListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class InsuranceEnquiriesService(BaseService):
    """Service for insurance enquiries operations."""

    def __init__(self, session: AsyncSession):
        repository = InsuranceEnquiriesRepository(session)
        super().__init__(repository, session)

    async def create_insurance_enquiry(
        self,
        data: InsuranceEnquiryCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> InsuranceEnquiryResponse:
        """Create a new insurance enquiry."""
        logger.info(f"Creating insurance enquiry for: {data.customer_name}")
        enquiry_data = data.model_dump()
        enquiry = await self.repository.create(enquiry_data, created_by, created_ip)
        enquiry_dict = self._model_to_dict(enquiry)
        return InsuranceEnquiryResponse(**enquiry_dict)

    async def get_insurance_enquiry_by_id(self, enquiry_id: UUID) -> Optional[InsuranceEnquiryResponse]:
        """Get insurance enquiry by ID."""
        enquiry = await self.repository.get_by_id(enquiry_id)
        if not enquiry:
            return None
        enquiry_dict = self._model_to_dict(enquiry)
        return InsuranceEnquiryResponse(**enquiry_dict)

    async def get_insurance_enquiries_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> InsuranceEnquiryListResponse:
        """Get list of insurance enquiries with pagination, search, and sort."""
        additional_filters = {}
        if status:
            additional_filters["status"] = status
        if user_id:
            additional_filters["created_by"] = user_id

        enquiries, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional_filters if additional_filters else None
        )

        enquiry_responses = [
            InsuranceEnquiryResponse(**self._model_to_dict(e)) for e in enquiries
        ]
        return InsuranceEnquiryListResponse(
            items=enquiry_responses,
            pagination=PaginationResponse(**pagination)
        )

    async def update_insurance_enquiry(
        self,
        enquiry_id: UUID,
        data: InsuranceEnquiryUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[InsuranceEnquiryResponse]:
        """Update an insurance enquiry."""
        logger.info(f"Updating insurance enquiry: {enquiry_id}")
        enquiry_data = data.model_dump(exclude_unset=True)
        enquiry = await self.repository.update(enquiry_id, enquiry_data, updated_by, updated_ip)
        if not enquiry:
            return None
        enquiry_dict = self._model_to_dict(enquiry)
        return InsuranceEnquiryResponse(**enquiry_dict)

    async def delete_insurance_enquiry(
        self,
        enquiry_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete an insurance enquiry."""
        logger.info(f"Deleting insurance enquiry: {enquiry_id}")
        return await self.repository.soft_delete(enquiry_id, updated_by, updated_ip)
