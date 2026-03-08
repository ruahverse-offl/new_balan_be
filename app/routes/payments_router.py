"""
Payments Router
FastAPI routes for payments resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.payments_service import PaymentsService
from app.schemas.payments_schema import (
    PaymentCreateRequest,
    PaymentUpdateRequest,
    PaymentResponse,
    PaymentListResponse
)
from app.utils.rbac import require_permission, require_any_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PaymentResponse)
async def create_payment(
    data: PaymentCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PAYMENT_PROCESS"))
):
    """Create a new payment."""
    ip_address = get_client_ip(request)
    service = PaymentsService(db)
    payment = await service.create_payment(data, current_user_id, ip_address)
    return payment


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_by_id(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_any_permission(["PAYMENT_PROCESS", "ORDER_VIEW"]))
):
    """Get payment by ID. Allowed for PAYMENT_PROCESS or ORDER_VIEW (e.g. staff viewing payments)."""
    service = PaymentsService(db)
    payment = await service.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found"
        )
    return payment


@router.get("/", response_model=PaymentListResponse)
async def get_payments_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_any_permission(["PAYMENT_PROCESS", "ORDER_VIEW"]))
):
    """Get list of payments. Allowed for PAYMENT_PROCESS or ORDER_VIEW (so staff with order view can see payments)."""
    service = PaymentsService(db)
    result = await service.get_payments_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )
    return result


@router.patch("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: UUID,
    data: PaymentUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PAYMENT_PROCESS"))
):
    """Update a payment."""
    ip_address = get_client_ip(request)
    service = PaymentsService(db)
    payment = await service.update_payment(payment_id, data, current_user_id, ip_address)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found"
        )
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_200_OK)
async def delete_payment(
    payment_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PAYMENT_PROCESS"))
):
    """Soft delete a payment."""
    ip_address = get_client_ip(request)
    service = PaymentsService(db)
    deleted = await service.delete_payment(payment_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found"
        )
    return {"message": "Payment deleted successfully", "id": str(payment_id)}
