"""
Orders Router
FastAPI routes for orders resource
"""

from typing import Optional, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.orders_service import OrdersService
from app.schemas.orders_schema import (
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderResponse,
    OrderListResponse,
    OrderDetailResponse,
    OrderSalesSummaryResponse,
)
from app.utils.auth import get_current_user_id, get_current_user_id_optional
from app.utils.rbac import RBACService
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


async def _can_view_all_orders(rbac: RBACService, user_id: UUID) -> bool:
    """Staff who see all payments should see all orders too — same as order list read."""
    if await rbac.has_module_action(user_id, "orders", "read"):
        return True
    if await rbac.has_module_action(user_id, "payments", "update"):
        return True
    return False


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
async def create_order(
    data: OrderCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Create a new order.

    Requires a valid JWT (no guest checkout). Callers must have ``ORDER_CREATE``.
    Storefront roles (**PUBLIC**, **CUSTOMER**) must set ``customer_id`` to the
    logged-in user so orders cannot be placed for another account.
    """
    rbac_service = RBACService(db)
    if not await rbac_service.has_module_action(current_user_id, "orders", "create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="orders:create (matrix) required to place an order",
        )
    role = await rbac_service.get_user_role(current_user_id)
    role_name = (role.name or "").upper() if role else ""
    if role_name in ("PUBLIC", "CUSTOMER") and str(data.customer_id) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="customer_id must match the logged-in user for storefront checkout",
        )
    ip_address = get_client_ip(request)
    service = OrdersService(db)
    order = await service.create_order(data, current_user_id, ip_address)
    return order


@router.get("/stats", response_model=OrderSalesSummaryResponse)
async def get_orders_stats(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Aggregated sales figures: delivered / returned / cancelled / net. Staff only."""
    rbac_service = RBACService(db)
    if not await _can_view_all_orders(rbac_service, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="orders:read permission required",
        )
    service = OrdersService(db)
    return await service.get_sales_summary()


@router.get("/{order_id}/detail", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Get full order detail (order + items + payment) for admin/refund reference."""
    rbac_service = RBACService(db)
    service = OrdersService(db)
    detail = await service.get_order_detail(order_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    if await _can_view_all_orders(rbac_service, current_user_id):
        return detail
    if str(detail.order.customer_id) == str(current_user_id):
        return detail
    has_delivery_access = await rbac_service.has_module_action(
        current_user_id, "delivery-orders", "read"
    ) or await rbac_service.has_module_action(current_user_id, "delivery-orders", "update")
    if has_delivery_access and detail.order.delivery_assigned_user_id and str(detail.order.delivery_assigned_user_id) == str(current_user_id):
        return detail
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only view your own orders"
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Get order by ID."""
    service = OrdersService(db)
    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    # Check if user owns the order or has staff-wide order/payment view
    if current_user_id:
        rbac_service = RBACService(db)
        if await _can_view_all_orders(rbac_service, current_user_id):
            return order
        if str(order.customer_id) == str(current_user_id):
            return order
        has_delivery_access = await rbac_service.has_module_action(
        current_user_id, "delivery-orders", "read"
    ) or await rbac_service.has_module_action(current_user_id, "delivery-orders", "update")
        if has_delivery_access and order.delivery_assigned_user_id and str(order.delivery_assigned_user_id) == str(current_user_id):
            return order
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders"
        )
    return order


@router.get("/", response_model=OrderListResponse)
async def get_orders_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    order_status: Optional[str] = Query(default=None, description="Filter by exact order status (e.g. PENDING, DELIVERED)"),
    order_date: Optional[str] = Query(default=None, description="Filter by creation date (YYYY-MM-DD, IST)"),
    delivery_list_scope: Optional[Literal["active", "history"]] = Query(
        default=None,
        description=(
            "Delivery agents only: `active` = in-progress runs (assigned → out for delivery); "
            "`history` = delivered or returned to store. Ignored for staff/customer lists. "
            "When omitted for delivery agents, defaults to `active`."
        ),
    ),
    staff_scope: Optional[Literal["active", "history"]] = Query(
        default=None,
        description="Staff only: `active` = non-terminal orders; `history` = delivered/returned/cancelled/refunded.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Get list of orders. Authentication required.

    - ORDER_VIEW or PAYMENT_PROCESS: all orders (aligned with payments list).
    - DELIVERY_ORDER_VIEW or DELIVERY_ORDER_UPDATE (without the above): orders assigned to the current user.
    - Otherwise: orders where customer_id is the current user.

    For delivery-scoped users, ``delivery_list_scope`` filters by fulfillment stage (active vs history).
    """
    rbac_service = RBACService(db)
    has_full_list = await _can_view_all_orders(rbac_service, current_user_id)
    has_delivery_scope = await rbac_service.has_module_action(
        current_user_id, "delivery-orders", "read"
    ) or await rbac_service.has_module_action(current_user_id, "delivery-orders", "update")

    user_id_filter = None
    delivery_assigned_filter = None
    if has_full_list:
        user_id_filter = None
    elif has_delivery_scope:
        delivery_assigned_filter = current_user_id
    else:
        user_id_filter = current_user_id

    delivery_agent_status_scope: Optional[str] = None
    if delivery_assigned_filter is not None and not has_full_list:
        delivery_agent_status_scope = delivery_list_scope or "active"

    service = OrdersService(db)
    result = await service.get_orders_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        user_id=user_id_filter,
        delivery_assigned_user_id=delivery_assigned_filter,
        delivery_agent_status_scope=delivery_agent_status_scope,
        staff_scope=staff_scope if has_full_list else None,
        order_status=order_status or None,
        order_date=order_date or None,
    )
    return result


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    data: OrderUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Update an order (lifecycle transitions require ORDER_UPDATE or DELIVERY_ORDER_UPDATE)."""
    ip_address = get_client_ip(request)
    rbac_service = RBACService(db)
    can_order_update = await rbac_service.has_module_action(current_user_id, "orders", "update")
    can_delivery_update = await rbac_service.has_module_action(
        current_user_id, "delivery-orders", "update"
    )
    service = OrdersService(db)
    order = await service.update_order(
        order_id,
        data,
        current_user_id,
        ip_address,
        can_order_update=can_order_update,
        can_delivery_update=can_delivery_update,
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    return order


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
async def delete_order(
    order_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Soft delete an order."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = OrdersService(db)
    deleted = await service.delete_order(order_id, user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    return {"message": "Order deleted successfully", "id": str(order_id)}
