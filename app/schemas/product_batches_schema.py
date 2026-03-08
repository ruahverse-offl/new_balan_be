"""
Product Batches Schema
Pydantic models for product_batches resource
"""

from typing import Optional, List
from pydantic import Field, BaseModel
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class ProductBatchCreateRequest(BaseCreateRequest):
    """Request model for creating a product batch."""
    
    medicine_brand_id: UUID = Field(..., description="Medicine Brand ID")
    batch_number: str = Field(..., max_length=100, description="Batch number")
    expiry_date: date = Field(..., description="Expiry date")
    purchase_price: Decimal = Field(..., description="Purchase price (2 decimal places)")
    quantity_available: int = Field(..., description="Quantity available")
    
    model_config = {"json_schema_extra": {"example": {
        "medicine_brand_id": "mb1e123-4567-8901-2345-678901234567",
        "batch_number": "BATCH-0925",
        "expiry_date": "2026-09-30",
        "purchase_price": 18.50,
        "quantity_available": 120
    }}}


class ProductBatchUpdateRequest(BaseUpdateRequest):
    """Request model for updating a product batch."""
    
    medicine_brand_id: Optional[UUID] = Field(None, description="Medicine Brand ID")
    batch_number: Optional[str] = Field(None, max_length=100, description="Batch number")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    purchase_price: Optional[Decimal] = Field(None, description="Purchase price (2 decimal places)")
    quantity_available: Optional[int] = Field(None, description="Quantity available")
    
    model_config = {"json_schema_extra": {"example": {
        "batch_number": "BATCH-1025",
        "expiry_date": "2027-09-30",
        "purchase_price": 20.00,
        "quantity_available": 150
    }}}


class ProductBatchResponse(BaseResponse):
    """Response model for product batch."""
    
    id: UUID = Field(..., description="Product Batch ID")
    medicine_brand_id: UUID = Field(..., description="Medicine Brand ID")
    batch_number: str = Field(..., description="Batch number")
    expiry_date: date = Field(..., description="Expiry date")
    purchase_price: Decimal = Field(..., description="Purchase price")
    quantity_available: int = Field(..., description="Quantity available")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "pb1e123-4567-8901-2345-678901234567",
        "medicine_brand_id": "mb1e123-4567-8901-2345-678901234567",
        "batch_number": "BATCH-0925",
        "expiry_date": "2026-09-30",
        "purchase_price": 18.50,
        "quantity_available": 120,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class ProductBatchListResponse(ListResponse[ProductBatchResponse]):
    """Response model for product batch list with pagination."""
    pass


# ----- Batch detail (for row click: full batch info + transactions + order items using this batch) -----
class BatchDetailTransactionSummary(BaseModel):
    """One inventory transaction for this batch."""
    id: UUID = Field(..., description="Transaction ID")
    transaction_type: str = Field(..., description="PURCHASE, SALE, etc.")
    quantity_change: int = Field(..., description="Quantity change")
    reference_order_id: Optional[UUID] = Field(None, description="Order ID if SALE")
    remarks: Optional[str] = Field(None, description="Remarks")
    created_at: Optional[datetime] = Field(None, description="When")


class BatchDetailOrderItemSummary(BaseModel):
    """One order item that used this batch."""
    id: UUID = Field(..., description="Order item ID")
    order_id: UUID = Field(..., description="Order ID")
    order_reference: Optional[str] = Field(None, description="Order reference (date_time_username)")
    medicine_name: Optional[str] = Field(None, description="Medicine name")
    brand_name: Optional[str] = Field(None, description="Brand name")
    quantity: int = Field(..., description="Quantity sold")
    unit_price: Optional[Decimal] = Field(None, description="Unit price")
    total_price: Optional[Decimal] = Field(None, description="Total price")
    created_at: Optional[datetime] = Field(None, description="When order was placed")


class ProductBatchDetailResponse(BaseModel):
    """Full batch detail: batch info + all transactions for this batch + all order items that used this batch."""
    batch: ProductBatchResponse = Field(..., description="Batch details")
    transactions: List[BatchDetailTransactionSummary] = Field(default_factory=list, description="Inventory transactions for this batch")
    order_items: List[BatchDetailOrderItemSummary] = Field(default_factory=list, description="Order lines that used this batch")
