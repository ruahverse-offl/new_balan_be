"""
Order Items Router
FastAPI routes for order_items resource
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.order_items_service import OrderItemsService
from app.schemas.order_items_schema import (
    OrderItemCreateRequest,
    OrderItemUpdateRequest,
    OrderItemResponse,
    OrderItemListResponse
)
from app.utils.rbac import require_permission, require_any_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/order-items", tags=["order-items"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OrderItemResponse)
async def create_order_item(
    data: OrderItemCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ORDER_CREATE"))
):
    """Create a new order item."""
    ip_address = get_client_ip(request)
    service = OrderItemsService(db)
    item = await service.create_order_item(data, current_user_id, ip_address)
    return item


@router.post("/bulk", status_code=status.HTTP_201_CREATED, response_model=List[OrderItemResponse])
async def create_order_items_bulk(
    items: List[OrderItemCreateRequest],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ORDER_CREATE"))
):
    """Create multiple order items in bulk."""
    ip_address = get_client_ip(request)
    service = OrderItemsService(db)
    items_result = await service.create_order_items_bulk(items, current_user_id, ip_address)
    return items_result


@router.get("/{item_id}", response_model=OrderItemResponse)
async def get_order_item_by_id(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_any_permission(["ORDER_VIEW", "PAYMENT_PROCESS"]))
):
    """Get order item by ID."""
    service = OrderItemsService(db)
    item = await service.get_order_item_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order item with ID {item_id} not found"
        )
    return item


@router.get("/", response_model=OrderItemListResponse)
async def get_order_items_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    order_id: Optional[UUID] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_any_permission(["ORDER_VIEW", "PAYMENT_PROCESS"]))
):
    """Get list of order items with pagination, search, and sort."""
    service = OrderItemsService(db)
    result = await service.get_order_items_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        order_id=order_id
    )
    return result


@router.patch("/{item_id}", response_model=OrderItemResponse)
async def update_order_item(
    item_id: UUID,
    data: OrderItemUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ORDER_UPDATE"))
):
    """Update an order item."""
    ip_address = get_client_ip(request)
    service = OrderItemsService(db)
    item = await service.update_order_item(item_id, data, current_user_id, ip_address)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order item with ID {item_id} not found"
        )
    return item


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_order_item(
    item_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ORDER_UPDATE"))
):
    """Soft delete an order item."""
    ip_address = get_client_ip(request)
    service = OrderItemsService(db)
    deleted = await service.delete_order_item(item_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order item with ID {item_id} not found"
        )
    return {"message": "Order item deleted successfully", "id": str(item_id)}
