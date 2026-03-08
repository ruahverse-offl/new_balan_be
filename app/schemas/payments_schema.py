"""
Payments Schema
Pydantic models for payments resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class PaymentCreateRequest(BaseCreateRequest):
    """Request model for creating a payment."""
    
    order_id: UUID = Field(..., description="Order ID")
    payment_method: str = Field(..., max_length=50, description="Payment method (e.g., UPI, CASH)")
    payment_status: str = Field(..., max_length=50, description="Payment status (e.g., PENDING)")
    amount: Decimal = Field(..., description="Payment amount (2 decimal places)")
    
    model_config = {"json_schema_extra": {"example": {
        "order_id": "o1e123-4567-8901-2345-678901234567",
        "payment_method": "UPI",
        "payment_status": "PENDING",
        "amount": 299.00
    }}}


class PaymentUpdateRequest(BaseUpdateRequest):
    """Request model for updating a payment."""
    
    order_id: Optional[UUID] = Field(None, description="Order ID")
    payment_method: Optional[str] = Field(None, max_length=50, description="Payment method")
    payment_status: Optional[str] = Field(None, max_length=50, description="Payment status")
    amount: Optional[Decimal] = Field(None, description="Payment amount (2 decimal places)")
    
    model_config = {"json_schema_extra": {"example": {
        "payment_status": "SUCCESS",
        "amount": 299.00
    }}}


class PaymentResponse(BaseResponse):
    """Response model for payment — full transaction details."""

    id: UUID = Field(..., description="Payment ID")
    order_id: UUID = Field(..., description="Order ID")
    payment_method: str = Field(..., description="Payment method")
    payment_status: str = Field(..., description="Payment status")
    amount: Decimal = Field(..., description="Payment amount")

    # Transaction tracking
    merchant_transaction_id: Optional[str] = Field(None, description="Our transaction ID sent to gateway")
    gateway_transaction_id: Optional[str] = Field(None, description="Gateway's transaction ID")
    gateway_order_id: Optional[str] = Field(None, description="Gateway's order ID")
    payment_date: Optional[datetime] = Field(None, description="When payment was completed")

    # Refund tracking
    refund_status: str = Field(default="NONE", description="NONE / INITIATED / COMPLETED / FAILED")
    refund_amount: Decimal = Field(default=0, description="Refund amount")
    refund_transaction_id: Optional[str] = Field(None, description="Refund transaction ID")

    model_config = {"json_schema_extra": {"example": {
        "id": "pay1e123-4567-8901-2345-678901234567",
        "order_id": "o1e123-4567-8901-2345-678901234567",
        "payment_method": "RAZORPAY",
        "payment_status": "SUCCESS",
        "amount": 299.00,
        "merchant_transaction_id": "abc123def456",
        "gateway_transaction_id": "T2302231234567890",
        "payment_date": "2026-02-28T14:30:00Z",
        "refund_status": "NONE",
        "refund_amount": 0,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class PaymentListResponse(ListResponse[PaymentResponse]):
    """Response model for payment list with pagination."""
    pass
