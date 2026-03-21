"""Pydantic models for inventory and low-stock alerts."""

from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class StockByOfferingItem(BaseModel):
    medicine_brand_offering_id: UUID
    stock_quantity: int = Field(ge=0)


class StockByOfferingResponse(BaseModel):
    items: List[StockByOfferingItem]


class InventoryAlertItem(BaseModel):
    id: str
    medicine_brand_offering_id: str
    medicine_name: str
    brand_name: str
    current_stock: int
    message: str = Field(
        default="",
        description="Human-readable alert line for dashboards",
    )
    created_at: str | None = None


class InventoryAlertListResponse(BaseModel):
    items: List[InventoryAlertItem]
    threshold: int = Field(description="INV_STOCK_THRESHOLD from server config")


class InventoryStockUpdateRequest(BaseModel):
    stock_quantity: int = Field(ge=0, description="Absolute on-hand units after update")
