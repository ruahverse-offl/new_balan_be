"""Routes for medicine_categories."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.medicine_categories_service import MedicineCategoriesService
from app.schemas.medicine_categories_schema import (
    MedicineCategoryCreateRequest,
    MedicineCategoryUpdateRequest,
    MedicineCategoryResponse,
    MedicineCategoryListResponse,
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/medicine-categories", tags=["medicine-categories"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MedicineCategoryResponse)
async def create_medicine_category(
    data: MedicineCategoryCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CATEGORY_MANAGE")),
):
    ip_address = get_client_ip(request)
    service = MedicineCategoriesService(db)
    return await service.create_category(data, current_user_id, ip_address)


@router.get("/{category_id}", response_model=MedicineCategoryResponse)
async def get_medicine_category_by_id(category_id: UUID, db: AsyncSession = Depends(get_db)):
    service = MedicineCategoriesService(db)
    row = await service.get_category_by_id(category_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine category not found")
    return row


@router.get("/", response_model=MedicineCategoryListResponse)
async def list_medicine_categories(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    service = MedicineCategoriesService(db)
    return await service.get_categories_list(limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order)


@router.patch("/{category_id}", response_model=MedicineCategoryResponse)
async def update_medicine_category(
    category_id: UUID,
    data: MedicineCategoryUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CATEGORY_MANAGE")),
):
    ip_address = get_client_ip(request)
    service = MedicineCategoriesService(db)
    row = await service.update_category(category_id, data, current_user_id, ip_address)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine category not found")
    return row


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_medicine_category(
    category_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CATEGORY_MANAGE")),
):
    ip_address = get_client_ip(request)
    service = MedicineCategoriesService(db)
    if not await service.delete_category(category_id, current_user_id, ip_address):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine category not found")
    return {"message": "Medicine category deleted successfully", "id": str(category_id)}
