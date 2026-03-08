"""
Product Batches Router
FastAPI routes for product_batches resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.product_batches_service import ProductBatchesService
from app.schemas.product_batches_schema import (
    ProductBatchCreateRequest,
    ProductBatchUpdateRequest,
    ProductBatchResponse,
    ProductBatchListResponse,
    ProductBatchDetailResponse,
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/product-batches", tags=["product-batches"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductBatchResponse)
async def create_product_batch(
    data: ProductBatchCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CREATE"))
):
    """Create a new product batch."""
    ip_address = get_client_ip(request)
    service = ProductBatchesService(db)
    batch = await service.create_product_batch(data, current_user_id, ip_address)
    return batch


@router.get("/{batch_id}/detail", response_model=ProductBatchDetailResponse)
async def get_batch_detail(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("MEDICINE_VIEW"))
):
    """Get full batch detail: batch info + inventory transactions for this batch + order items that used this batch."""
    service = ProductBatchesService(db)
    detail = await service.get_batch_detail(batch_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product batch with ID {batch_id} not found"
        )
    return detail


@router.get("/{batch_id}", response_model=ProductBatchResponse)
async def get_product_batch_by_id(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get product batch by ID."""
    service = ProductBatchesService(db)
    batch = await service.get_product_batch_by_id(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product batch with ID {batch_id} not found"
        )
    return batch


@router.get("/", response_model=ProductBatchListResponse)
async def get_product_batches_list(
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of product batches with pagination, search, and sort."""
    service = ProductBatchesService(db)
    result = await service.get_product_batches_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )
    return result


@router.patch("/{batch_id}", response_model=ProductBatchResponse)
async def update_product_batch(
    batch_id: UUID,
    data: ProductBatchUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_UPDATE"))
):
    """Update a product batch."""
    ip_address = get_client_ip(request)
    service = ProductBatchesService(db)
    batch = await service.update_product_batch(batch_id, data, current_user_id, ip_address)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product batch with ID {batch_id} not found"
        )
    return batch


@router.delete("/{batch_id}", status_code=status.HTTP_200_OK)
async def delete_product_batch(
    batch_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_DELETE"))
):
    """Soft delete a product batch."""
    ip_address = get_client_ip(request)
    service = ProductBatchesService(db)
    deleted = await service.delete_product_batch(batch_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product batch with ID {batch_id} not found"
        )
    return {"message": "Product batch deleted successfully", "id": str(batch_id)}
