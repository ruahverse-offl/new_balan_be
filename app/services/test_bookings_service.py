"""
Test Bookings Service
Business logic layer for test_bookings
"""

from typing import Optional
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.repositories.test_bookings_repository import TestBookingsRepository
from app.schemas.test_bookings_schema import (
    TestBookingCreateRequest,
    TestBookingUpdateRequest,
    TestBookingResponse,
    TestBookingListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.db.models import PolyclinicTest

logger = logging.getLogger(__name__)


class TestBookingsService(BaseService):
    """Service for test_bookings operations."""
    
    def __init__(self, session: AsyncSession):
        repository = TestBookingsRepository(session)
        super().__init__(repository, session)
    
    async def create_test_booking(
        self,
        data: TestBookingCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> TestBookingResponse:
        """Create a new test booking."""
        logger.info(f"Creating test booking for patient: {data.patient_name}")
        booking_data = data.model_dump()
        booking = await self.repository.create(booking_data, created_by, created_ip)
        booking_dict = self._model_to_dict(booking)
        return TestBookingResponse(**booking_dict)
    
    async def get_test_booking_by_id(self, booking_id: UUID) -> Optional[TestBookingResponse]:
        """Get test booking by ID."""
        booking = await self.repository.get_by_id(booking_id)
        if not booking:
            return None
        booking_dict = self._model_to_dict(booking)
        return TestBookingResponse(**booking_dict)
    
    async def get_test_bookings_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        test_id: Optional[UUID] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> TestBookingListResponse:
        """Get list of test bookings with pagination, search, and sort."""
        additional_filters = {}
        if test_id:
            additional_filters["test_id"] = test_id
        if status:
            additional_filters["status"] = status
        
        bookings, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters=additional_filters if additional_filters else None
        )
        
        # Filter by date range if provided
        if date_from or date_to:
            filtered = []
            for booking in bookings:
                if date_from and booking.booking_date < date_from:
                    continue
                if date_to and booking.booking_date > date_to:
                    continue
                filtered.append(booking)
            bookings = filtered

        test_ids = [b.test_id for b in bookings if b.test_id]
        name_by_test_id = {}
        if test_ids:
            stmt = select(PolyclinicTest.id, PolyclinicTest.name).where(
                PolyclinicTest.id.in_(test_ids),
                PolyclinicTest.is_deleted == False
            )
            result = await self.session.execute(stmt)
            for row in result:
                name_by_test_id[str(row.id)] = row.name or "—"

        booking_responses = []
        for b in bookings:
            d = self._model_to_dict(b)
            d["test_name"] = name_by_test_id.get(str(b.test_id), "—")
            booking_responses.append(TestBookingResponse(**d))
        return TestBookingListResponse(
            items=booking_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_test_booking(
        self,
        booking_id: UUID,
        data: TestBookingUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[TestBookingResponse]:
        """Update a test booking."""
        logger.info(f"Updating test booking: {booking_id}")
        booking_data = data.model_dump(exclude_unset=True)
        booking = await self.repository.update(booking_id, booking_data, updated_by, updated_ip)
        if not booking:
            return None
        booking_dict = self._model_to_dict(booking)
        return TestBookingResponse(**booking_dict)
    
    async def delete_test_booking(
        self,
        booking_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a test booking."""
        logger.info(f"Deleting test booking: {booking_id}")
        return await self.repository.soft_delete(booking_id, updated_by, updated_ip)
