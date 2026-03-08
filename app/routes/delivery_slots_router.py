"""
Delivery Slots Router
FastAPI routes for delivery_slots resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.delivery_slots_service import DeliverySlotsService
from app.schemas.delivery_slots_schema import (
    DeliverySlotCreateRequest,
    DeliverySlotUpdateRequest,
    DeliverySlotResponse,
    DeliverySlotListResponse
)
from app.utils.auth import get_current_user_id_optional
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/delivery-slots", tags=["delivery-slots"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DeliverySlotResponse)
async def create_delivery_slot(
    data: DeliverySlotCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Create a new delivery slot."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = DeliverySlotsService(db)
    slot = await service.create_delivery_slot(data, user_id, ip_address)
    return slot


@router.get("/{slot_id}", response_model=DeliverySlotResponse)
async def get_delivery_slot_by_id(
    slot_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get delivery slot by ID."""
    service = DeliverySlotsService(db)
    slot = await service.get_delivery_slot_by_id(slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery slot with ID {slot_id} not found"
        )
    return slot


@router.get("/", response_model=DeliverySlotListResponse)
async def get_delivery_slots_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="slot_order"),
    sort_order: Optional[str] = Query(default="asc", pattern="^(asc|desc)$"),
    delivery_settings_id: Optional[UUID] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of delivery slots with pagination, search, and sort."""
    service = DeliverySlotsService(db)
    result = await service.get_delivery_slots_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        delivery_settings_id=delivery_settings_id, is_active=is_active
    )
    return result


@router.patch("/{slot_id}", response_model=DeliverySlotResponse)
async def update_delivery_slot(
    slot_id: UUID,
    data: DeliverySlotUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Update a delivery slot."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = DeliverySlotsService(db)
    slot = await service.update_delivery_slot(slot_id, data, user_id, ip_address)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery slot with ID {slot_id} not found"
        )
    return slot


@router.delete("/{slot_id}", status_code=status.HTTP_200_OK)
async def delete_delivery_slot(
    slot_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Soft delete a delivery slot."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = DeliverySlotsService(db)
    deleted = await service.delete_delivery_slot(slot_id, user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery slot with ID {slot_id} not found"
        )
    return {"message": "Delivery slot deleted successfully", "id": str(slot_id)}
