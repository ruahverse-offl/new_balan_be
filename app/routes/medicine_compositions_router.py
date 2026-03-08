"""
Medicine Compositions Router
FastAPI routes for medicine_compositions resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.medicine_compositions_service import MedicineCompositionsService
from app.schemas.medicine_compositions_schema import (
    MedicineCompositionCreateRequest,
    MedicineCompositionUpdateRequest,
    MedicineCompositionResponse,
    MedicineCompositionListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/medicine-compositions", tags=["medicine-compositions"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MedicineCompositionResponse)
async def create_medicine_composition(
    data: MedicineCompositionCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CREATE"))
):
    """Create a new medicine composition."""
    ip_address = get_client_ip(request)
    service = MedicineCompositionsService(db)
    composition = await service.create_medicine_composition(data, current_user_id, ip_address)
    return composition


@router.get("/{composition_id}", response_model=MedicineCompositionResponse)
async def get_medicine_composition_by_id(
    composition_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get medicine composition by ID."""
    service = MedicineCompositionsService(db)
    composition = await service.get_medicine_composition_by_id(composition_id)
    if not composition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine composition with ID {composition_id} not found"
        )
    return composition


@router.get("/", response_model=MedicineCompositionListResponse)
async def get_medicine_compositions_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of medicine compositions with pagination, search, and sort."""
    service = MedicineCompositionsService(db)
    result = await service.get_medicine_compositions_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )
    return result


@router.patch("/{composition_id}", response_model=MedicineCompositionResponse)
async def update_medicine_composition(
    composition_id: UUID,
    data: MedicineCompositionUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_UPDATE"))
):
    """Update a medicine composition."""
    ip_address = get_client_ip(request)
    service = MedicineCompositionsService(db)
    composition = await service.update_medicine_composition(composition_id, data, current_user_id, ip_address)
    if not composition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine composition with ID {composition_id} not found"
        )
    return composition


@router.delete("/{composition_id}", status_code=status.HTTP_200_OK)
async def delete_medicine_composition(
    composition_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_DELETE"))
):
    """Soft delete a medicine composition."""
    ip_address = get_client_ip(request)
    service = MedicineCompositionsService(db)
    deleted = await service.delete_medicine_composition(composition_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine composition with ID {composition_id} not found"
        )
    return {"message": "Medicine composition deleted successfully", "id": str(composition_id)}
