"""
Inventory Transactions Router
FastAPI routes for inventory_transactions resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.inventory_transactions_service import InventoryTransactionsService
from app.schemas.inventory_transactions_schema import (
    InventoryTransactionCreateRequest,
    InventoryTransactionUpdateRequest,
    InventoryTransactionResponse,
    InventoryTransactionListResponse,
    InventoryTransactionDetailResponse,
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/inventory-transactions", tags=["inventory-transactions"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=InventoryTransactionResponse)
async def create_inventory_transaction(
    data: InventoryTransactionCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("INVENTORY_UPDATE"))
):
    """Create a new inventory transaction."""
    ip_address = get_client_ip(request)
    service = InventoryTransactionsService(db)
    transaction = await service.create_inventory_transaction(data, current_user_id, ip_address)
    return transaction


@router.get("/{transaction_id}/detail", response_model=InventoryTransactionDetailResponse)
async def get_inventory_transaction_detail(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("INVENTORY_VIEW"))
):
    """Get transaction detail with linked order summary (when reference_order_id is set)."""
    service = InventoryTransactionsService(db)
    detail = await service.get_inventory_transaction_detail(transaction_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory transaction with ID {transaction_id} not found"
        )
    return detail


@router.get("/{transaction_id}", response_model=InventoryTransactionResponse)
async def get_inventory_transaction_by_id(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("INVENTORY_VIEW"))
):
    """Get inventory transaction by ID."""
    service = InventoryTransactionsService(db)
    transaction = await service.get_inventory_transaction_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory transaction with ID {transaction_id} not found"
        )
    return transaction


@router.get("/", response_model=InventoryTransactionListResponse)
async def get_inventory_transactions_list(
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    medicine_brand_id: Optional[UUID] = Query(default=None, description="Filter by medicine brand (full history for that brand)"),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_permission("INVENTORY_VIEW"))
):
    """Get list of inventory transactions; optionally filter by medicine_brand_id for full history per brand."""
    service = InventoryTransactionsService(db)
    result = await service.get_inventory_transactions_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        medicine_brand_id=medicine_brand_id,
    )
    return result


@router.patch("/{transaction_id}", response_model=InventoryTransactionResponse)
async def update_inventory_transaction(
    transaction_id: UUID,
    data: InventoryTransactionUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("INVENTORY_UPDATE"))
):
    """Update an inventory transaction."""
    ip_address = get_client_ip(request)
    service = InventoryTransactionsService(db)
    transaction = await service.update_inventory_transaction(transaction_id, data, current_user_id, ip_address)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory transaction with ID {transaction_id} not found"
        )
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_200_OK)
async def delete_inventory_transaction(
    transaction_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("INVENTORY_UPDATE"))
):
    """Soft delete an inventory transaction."""
    ip_address = get_client_ip(request)
    service = InventoryTransactionsService(db)
    deleted = await service.delete_inventory_transaction(transaction_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory transaction with ID {transaction_id} not found"
        )
    return {"message": "Inventory transaction deleted successfully", "id": str(transaction_id)}
