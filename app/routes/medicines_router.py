"""
Medicines Router
FastAPI routes for medicines resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.medicines_service import MedicinesService
from app.schemas.medicines_schema import (
    MedicineCreateRequest,
    MedicineUpdateRequest,
    MedicineResponse,
    MedicineListResponse
)
from app.utils.auth import get_current_user_id_optional
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/medicines", tags=["medicines"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MedicineResponse)
async def create_medicine(
    data: MedicineCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Create a new medicine."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = MedicinesService(db)
    medicine = await service.create_medicine(data, user_id, ip_address)
    return medicine


@router.get("/{medicine_id}", response_model=MedicineResponse)
async def get_medicine_by_id(
    medicine_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get medicine by ID."""
    service = MedicinesService(db)
    medicine = await service.get_medicine_by_id(medicine_id)
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {medicine_id} not found"
        )
    return medicine


@router.get("/", response_model=MedicineListResponse)
async def get_medicines_list(
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of medicines with pagination, search, and sort."""
    service = MedicinesService(db)
    result = await service.get_medicines_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )
    return result


@router.patch("/{medicine_id}", response_model=MedicineResponse)
async def update_medicine(
    medicine_id: UUID,
    data: MedicineUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Update a medicine."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = MedicinesService(db)
    medicine = await service.update_medicine(medicine_id, data, user_id, ip_address)
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {medicine_id} not found"
        )
    return medicine


@router.delete("/{medicine_id}", status_code=status.HTTP_200_OK)
async def delete_medicine(
    medicine_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Soft delete a medicine."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = MedicinesService(db)
    deleted = await service.delete_medicine(medicine_id, user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {medicine_id} not found"
        )
    return {"message": "Medicine deleted successfully", "id": str(medicine_id)}
