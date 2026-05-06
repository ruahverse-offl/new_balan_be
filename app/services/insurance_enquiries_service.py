"""
Insurance Enquiries Service
Business logic layer for insurance_enquiries
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.insurance_enquiries_repository import InsuranceEnquiriesRepository
from app.schemas.insurance_enquiries_schema import (
    InsuranceEnquiryCreateRequest,
    InsuranceEnquiryUpdateRequest,
    InsuranceEnquiryResponse,
    InsuranceEnquiryListResponse,
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class InsuranceEnquiriesService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(InsuranceEnquiriesRepository(session), session)

    async def create_enquiry(
        self,
        data: InsuranceEnquiryCreateRequest,
        created_by: UUID,
        created_ip: str,
    ) -> InsuranceEnquiryResponse:
        logger.info("Creating insurance enquiry for %s", data.customer_name)
        enquiry = await self.repository.create(data.model_dump(), created_by, created_ip)
        return InsuranceEnquiryResponse(**self._model_to_dict(enquiry))

    async def get_enquiry_by_id(self, enquiry_id: UUID) -> Optional[InsuranceEnquiryResponse]:
        e = await self.repository.get_by_id(enquiry_id)
        if not e:
            return None
        return InsuranceEnquiryResponse(**self._model_to_dict(e))

    async def get_enquiries_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        status: Optional[str] = None,
    ) -> InsuranceEnquiryListResponse:
        additional_filters = {}
        if status:
            additional_filters["status"] = status
        items, pagination = await self.repository.get_list(
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            additional_filters=additional_filters or None,
        )
        return InsuranceEnquiryListResponse(
            items=[InsuranceEnquiryResponse(**self._model_to_dict(e)) for e in items],
            pagination=PaginationResponse(**pagination),
        )

    async def update_enquiry(
        self,
        enquiry_id: UUID,
        data: InsuranceEnquiryUpdateRequest,
        updated_by: UUID,
        updated_ip: str,
    ) -> Optional[InsuranceEnquiryResponse]:
        logger.info("Updating insurance enquiry %s", enquiry_id)
        e = await self.repository.update(enquiry_id, data.model_dump(exclude_unset=True), updated_by, updated_ip)
        if not e:
            return None
        return InsuranceEnquiryResponse(**self._model_to_dict(e))

    async def delete_enquiry(self, enquiry_id: UUID, updated_by: UUID, updated_ip: str) -> bool:
        logger.info("Deleting insurance enquiry %s", enquiry_id)
        return await self.repository.soft_delete(enquiry_id, updated_by, updated_ip)
