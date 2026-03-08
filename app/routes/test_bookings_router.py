"""
Test Bookings Router
FastAPI routes for test_bookings resource
"""

from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.test_bookings_service import TestBookingsService
from app.schemas.test_bookings_schema import (
    TestBookingCreateRequest,
    TestBookingUpdateRequest,
    TestBookingResponse,
    TestBookingListResponse
)
from app.utils.auth import get_current_user_id_optional
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/test-bookings", tags=["test-bookings"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TestBookingResponse)
async def create_test_booking(
    data: TestBookingCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Create a new test booking."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = TestBookingsService(db)
    booking = await service.create_test_booking(data, user_id, ip_address)
    await db.commit()
    return booking


@router.get("/{booking_id}", response_model=TestBookingResponse)
async def get_test_booking_by_id(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get test booking by ID."""
    service = TestBookingsService(db)
    booking = await service.get_test_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test booking with ID {booking_id} not found"
        )
    return booking


@router.get("/", response_model=TestBookingListResponse)
async def get_test_bookings_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    test_id: Optional[UUID] = Query(default=None),
    status: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("APPOINTMENT_VIEW"))
):
    """Get list of test bookings. Requires APPOINTMENT_VIEW permission."""
    service = TestBookingsService(db)
    result = await service.get_test_bookings_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        test_id=test_id, status=status, date_from=date_from, date_to=date_to
    )
    return result


@router.patch("/{booking_id}", response_model=TestBookingResponse)
async def update_test_booking(
    booking_id: UUID,
    data: TestBookingUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("APPOINTMENT_UPDATE"))
):
    """Update a test booking. Requires APPOINTMENT_UPDATE permission."""
    ip_address = get_client_ip(request)
    service = TestBookingsService(db)
    booking = await service.update_test_booking(booking_id, data, current_user_id, ip_address)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test booking with ID {booking_id} not found"
        )
    await db.commit()
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
async def delete_test_booking(
    booking_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("APPOINTMENT_DELETE"))
):
    """Soft delete a test booking. Requires APPOINTMENT_DELETE permission."""
    ip_address = get_client_ip(request)
    service = TestBookingsService(db)
    deleted = await service.delete_test_booking(booking_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test booking with ID {booking_id} not found"
        )
    return {"message": "Test booking deleted successfully", "id": str(booking_id)}
