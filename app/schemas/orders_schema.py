"""
Orders Schema
Pydantic models for orders resource
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse
from app.schemas.order_items_schema import OrderItemResponse
from app.schemas.payments_schema import PaymentResponse


class OrderCreateRequest(BaseCreateRequest):
    """Request model for creating an order."""

    customer_id: Optional[UUID] = Field(None, description="Customer ID (User ID)")
    customer_name: Optional[str] = Field(None, max_length=255, description="Customer name")
    customer_phone: str = Field(..., max_length=15, description="Customer phone number")
    customer_email: Optional[str] = Field(None, max_length=255, description="Customer email")
    delivery_address: str = Field(..., description="Delivery address")
    pincode: Optional[str] = Field(None, max_length=10, description="PIN code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    order_status: str = Field(
        default="PENDING",
        max_length=50,
        description="Lifecycle status; PENDING = payment pending, ORDER_RECEIVED = staff queue after payment",
    )
    total_amount: Decimal = Field(..., description="Subtotal before discounts")
    discount_amount: Decimal = Field(default=0, description="Discount amount")
    delivery_fee: Decimal = Field(default=0, description="Delivery fee")
    final_amount: Decimal = Field(..., description="Final amount after discounts + delivery")
    payment_method: str = Field(..., max_length=50, description="Payment method (RAZORPAY, CASH, UPI)")
    processed_by: Optional[UUID] = Field(None, description="Staff user who processed the order")
    notes: Optional[str] = Field(None, description="Order notes")
    prescription_path: Optional[str] = Field(None, description="Stored path/URL for prescription file if any")
    delivery_assigned_user_id: Optional[UUID] = Field(None, description="Delivery agent (set when assigning)")

    model_config = {"json_schema_extra": {"example": {
        "customer_name": "Ravi Kumar",
        "customer_phone": "9876543210",
        "delivery_address": "123 Main St, Chennai",
        "order_status": "PENDING",
        "total_amount": 350.00,
        "discount_amount": 50.00,
        "delivery_fee": 30.00,
        "final_amount": 330.00,
        "payment_method": "RAZORPAY",
    }}}


class OrderUpdateRequest(BaseUpdateRequest):
    """Request model for updating an order."""

    customer_id: Optional[UUID] = Field(None, description="Customer ID (User ID)")
    customer_name: Optional[str] = Field(None, max_length=255, description="Customer name")
    customer_phone: Optional[str] = Field(None, max_length=15, description="Customer phone number")
    customer_email: Optional[str] = Field(None, max_length=255, description="Customer email")
    delivery_address: Optional[str] = Field(None, description="Delivery address")
    pincode: Optional[str] = Field(None, max_length=10, description="PIN code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    order_status: Optional[str] = Field(None, max_length=50, description="Order lifecycle status")
    delivery_assigned_user_id: Optional[UUID] = Field(None, description="Assign delivery agent (with DELIVERY_ASSIGNED)")
    cancellation_reason: Optional[str] = Field(None, description="Required when setting CANCELLED_BY_STAFF")
    return_reason: Optional[str] = Field(None, description="Reason when customer refused delivery (DELIVERY_RETURNED)")
    total_amount: Optional[Decimal] = Field(None, description="Subtotal before discounts")
    discount_amount: Optional[Decimal] = Field(None, description="Discount amount")
    delivery_fee: Optional[Decimal] = Field(None, description="Delivery fee")
    final_amount: Optional[Decimal] = Field(None, description="Final amount")
    payment_method: Optional[str] = Field(None, max_length=50, description="Payment method")
    processed_by: Optional[UUID] = Field(None, description="Staff user who processed the order")
    notes: Optional[str] = Field(None, description="Order notes")
    prescription_path: Optional[str] = Field(None, description="Prescription file path/URL")

    model_config = {"json_schema_extra": {"example": {
        "order_status": "ORDER_TAKEN",
    }}}


class OrderResponse(BaseResponse):
    """Response model for order — all fields. id = UUID; order_reference = date_time_username."""

    id: UUID = Field(..., description="Order ID (UUID)")
    order_reference: Optional[str] = Field(None, description="Human-readable order id: date_time_username")
    customer_id: Optional[UUID] = Field(None, description="Customer ID (User ID)")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_phone: str = Field(..., description="Customer phone number")
    customer_email: Optional[str] = Field(None, description="Customer email")
    delivery_address: str = Field(..., description="Delivery address")
    pincode: Optional[str] = Field(None, description="PIN code")
    city: Optional[str] = Field(None, description="City")
    payment_completed_at: Optional[datetime] = Field(None, description="When payment was completed")
    order_status: str = Field(..., description="Order status")
    total_amount: Decimal = Field(..., description="Subtotal before discounts")
    discount_amount: Decimal = Field(..., description="Discount amount")
    delivery_fee: Decimal = Field(..., description="Delivery fee")
    final_amount: Decimal = Field(..., description="Final amount after discounts + delivery")
    payment_method: str = Field(..., description="Payment method")
    processed_by: Optional[UUID] = Field(None, description="Staff who processed")
    notes: Optional[str] = Field(None, description="Order notes")
    prescription_path: Optional[str] = Field(None, description="Prescription file path/URL")
    delivery_assigned_user_id: Optional[UUID] = Field(None, description="Assigned delivery user id")
    cancellation_reason: Optional[str] = Field(None, description="Why staff cancelled (wrong Rx, etc.)")
    cancelled_by_user_id: Optional[UUID] = Field(None, description="Staff who cancelled")
    cancelled_at: Optional[datetime] = Field(None, description="When staff cancelled")
    return_reason: Optional[str] = Field(None, description="Why delivery was returned / refused")

    model_config = {"json_schema_extra": {"example": {
        "id": "o1e12345-6789-0123-4567-890123456789",
        "customer_id": "u123e456-7890-1234-5678-901234567890",
        "customer_name": "Ravi Kumar",
        "customer_phone": "9876543210",
        "delivery_address": "123 Main St, Chennai",
        "order_status": "ORDER_RECEIVED",
        "total_amount": 350.00,
        "discount_amount": 50.00,
        "delivery_fee": 30.00,
        "final_amount": 330.00,
        "payment_method": "RAZORPAY",
        "processed_by": None,
        "notes": None,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False,
    }}}


class OrderDetailResponse(BaseModel):
    """Full order detail — order + items + payment. Used for 'View Order' screens."""

    order: OrderResponse = Field(..., description="Order details")
    items: List[OrderItemResponse] = Field(default_factory=list, description="Order items")
    payment: Optional[PaymentResponse] = Field(None, description="Payment details")

    model_config = {"json_schema_extra": {"example": {
        "order": {
            "id": "o1e12345-6789-0123-4567-890123456789",
            "customer_name": "Ravi Kumar",
            "customer_phone": "9876543210",
            "delivery_address": "123 Main St, Chennai",
            "order_status": "ORDER_RECEIVED",
            "total_amount": 350.00,
            "discount_amount": 50.00,
            "delivery_fee": 30.00,
            "final_amount": 330.00,
            "payment_method": "RAZORPAY",
        },
        "items": [
            {
                "id": "oi1e1234-5678-9012-3456-789012345678",
                "order_id": "o1e12345-6789-0123-4567-890123456789",
                "medicine_brand_id": "mb1e1234-5678-9012-3456-789012345678",
                "quantity": 2,
                "unit_price": 175.00,
                "total_price": 350.00,
                "requires_prescription": False,
            }
        ],
        "payment": {
            "id": "pay1e123-4567-8901-2345-678901234567",
            "payment_method": "RAZORPAY",
            "payment_status": "SUCCESS",
            "amount": 330.00,
            "merchant_transaction_id": "abc123def456",
            "gateway_transaction_id": "T2302231234567890",
        },
    }}}


class OrderListResponse(ListResponse[OrderResponse]):
    """Response model for order list with pagination."""

    pass
