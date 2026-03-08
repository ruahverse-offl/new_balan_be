"""
Inventory Transactions Schema
Pydantic models for inventory_transactions resource
"""

from typing import Optional
from pydantic import Field, BaseModel
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class InventoryTransactionCreateRequest(BaseCreateRequest):
    """Request model for creating an inventory transaction."""
    
    medicine_brand_id: UUID = Field(..., description="Medicine Brand ID")
    product_batch_id: UUID = Field(..., description="Product Batch ID")
    transaction_type: str = Field(..., max_length=50, description="Transaction type (e.g., SALE)")
    quantity_change: int = Field(..., description="Quantity change (positive for addition, negative for deduction)")
    reference_order_id: Optional[UUID] = Field(None, description="Reference Order ID")
    remarks: Optional[str] = Field(None, description="Transaction remarks")
    
    model_config = {"json_schema_extra": {"example": {
        "medicine_brand_id": "mb1e123-4567-8901-2345-678901234567",
        "product_batch_id": "pb1e123-4567-8901-2345-678901234567",
        "transaction_type": "SALE",
        "quantity_change": -10,
        "reference_order_id": "o1e123-4567-8901-2345-678901234567",
        "remarks": "Sold to customer"
    }}}


class InventoryTransactionUpdateRequest(BaseUpdateRequest):
    """Request model for updating an inventory transaction."""
    
    medicine_brand_id: Optional[UUID] = Field(None, description="Medicine Brand ID")
    product_batch_id: Optional[UUID] = Field(None, description="Product Batch ID")
    transaction_type: Optional[str] = Field(None, max_length=50, description="Transaction type")
    quantity_change: Optional[int] = Field(None, description="Quantity change")
    reference_order_id: Optional[UUID] = Field(None, description="Reference Order ID")
    remarks: Optional[str] = Field(None, description="Transaction remarks")
    
    model_config = {"json_schema_extra": {"example": {
        "transaction_type": "RETURN",
        "quantity_change": 5,
        "remarks": "Customer return"
    }}}


class InventoryTransactionResponse(BaseResponse):
    """Response model for inventory transaction."""
    
    id: UUID = Field(..., description="Inventory Transaction ID")
    medicine_brand_id: UUID = Field(..., description="Medicine Brand ID")
    product_batch_id: UUID = Field(..., description="Product Batch ID")
    transaction_type: str = Field(..., description="Transaction type")
    quantity_change: int = Field(..., description="Quantity change")
    reference_order_id: Optional[UUID] = Field(None, description="Reference Order ID")
    remarks: Optional[str] = Field(None, description="Transaction remarks")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "it1e123-4567-8901-2345-678901234567",
        "medicine_brand_id": "mb1e123-4567-8901-2345-678901234567",
        "product_batch_id": "pb1e123-4567-8901-2345-678901234567",
        "transaction_type": "SALE",
        "quantity_change": -10,
        "reference_order_id": "o1e123-4567-8901-2345-678901234567",
        "remarks": "Sold to customer",
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class InventoryTransactionListResponse(ListResponse[InventoryTransactionResponse]):
    """Response model for inventory transaction list with pagination."""
    pass


# ----- Transaction detail (for row click: transaction + order summary when it's a SALE) -----
class OrderSummaryForTransaction(BaseModel):
    """Minimal order info when transaction has reference_order_id."""
    order_id: UUID = Field(..., description="Order ID")
    order_reference: Optional[str] = Field(None, description="Order reference (date_time_username)")
    customer_name: Optional[str] = Field(None, description="Customer name")
    order_status: Optional[str] = Field(None, description="Order status")
    final_amount: Optional[float] = Field(None, description="Final amount")
    created_at: Optional[datetime] = Field(None, description="Order date")


class InventoryTransactionDetailResponse(BaseModel):
    """Transaction detail with optional linked order summary."""
    transaction: InventoryTransactionResponse = Field(..., description="Transaction details")
    order_summary: Optional[OrderSummaryForTransaction] = Field(None, description="Linked order (when reference_order_id is set)")
