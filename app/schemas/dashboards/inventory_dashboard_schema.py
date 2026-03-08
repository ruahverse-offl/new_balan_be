"""
Inventory Dashboard Schema
Pydantic models for inventory dashboard responses
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID


class InventoryKPIs(BaseModel):
    """Key Performance Indicators for inventory dashboard."""
    
    total_stock_value: Decimal = Field(..., description="Total stock value in ₹")
    total_stock_quantity: int = Field(..., description="Total stock quantity in units")
    total_active_products: int = Field(..., description="Number of active products")
    total_batches: int = Field(..., description="Number of active batches")
    low_stock_count: int = Field(..., description="Number of low stock items")
    out_of_stock_count: int = Field(..., description="Number of out of stock items")
    expiring_soon_count: int = Field(..., description="Number of batches expiring soon")
    expired_count: int = Field(..., description="Number of expired batches")
    stock_turnover_rate: Optional[Decimal] = Field(None, description="Stock turnover rate")
    average_stock_value: Optional[Decimal] = Field(None, description="Average stock value per product")


class InventoryAlert(BaseModel):
    """Alert for inventory issues."""
    
    type: str = Field(..., description="Alert type: LOW_STOCK, OUT_OF_STOCK, EXPIRING_SOON, EXPIRED")
    severity: str = Field(..., description="Alert severity: WARNING, CRITICAL")
    message: str = Field(..., description="Alert message")
    medicine_brand_id: Optional[UUID] = Field(None, description="Medicine brand ID")
    medicine_brand_name: Optional[str] = Field(None, description="Medicine brand name")
    batch_id: Optional[UUID] = Field(None, description="Batch ID")
    batch_number: Optional[str] = Field(None, description="Batch number")
    current_quantity: Optional[int] = Field(None, description="Current quantity")
    threshold: Optional[int] = Field(None, description="Low stock threshold")
    expiry_date: Optional[str] = Field(None, description="Expiry date")


class ChartDataPoint(BaseModel):
    """Data point for charts."""
    
    date: Optional[str] = Field(None, description="Date for time-series charts")
    label: Optional[str] = Field(None, description="Label for categorical charts")
    value: Optional[Decimal] = Field(None, description="Numeric value")
    quantity: Optional[int] = Field(None, description="Quantity value")
    count: Optional[int] = Field(None, description="Count value")


class InventoryChartData(BaseModel):
    """Chart data for inventory dashboard."""
    
    stock_value_trend: Optional[List[ChartDataPoint]] = Field(None, description="Stock value over time")
    stock_by_category: Optional[List[ChartDataPoint]] = Field(None, description="Stock levels by category")
    top_products: Optional[List[ChartDataPoint]] = Field(None, description="Top products by stock value")
    stock_distribution: Optional[List[ChartDataPoint]] = Field(None, description="Stock distribution (low/normal/out)")
    expiry_timeline: Optional[List[ChartDataPoint]] = Field(None, description="Expiry timeline")
    stock_movement: Optional[List[ChartDataPoint]] = Field(None, description="Stock movement trend")
    stock_by_dosage_form: Optional[List[ChartDataPoint]] = Field(None, description="Stock by dosage form")


class InventoryDashboardResponse(BaseModel):
    """Complete inventory dashboard response."""
    
    kpis: InventoryKPIs = Field(..., description="Key Performance Indicators")
    alerts: List[InventoryAlert] = Field(default_factory=list, description="Inventory alerts")
    charts: InventoryChartData = Field(..., description="Chart data")
    
    model_config = {"json_schema_extra": {"example": {
        "kpis": {
            "total_stock_value": 1250000.00,
            "total_stock_quantity": 5000,
            "total_active_products": 150,
            "total_batches": 200,
            "low_stock_count": 15,
            "out_of_stock_count": 5,
            "expiring_soon_count": 8,
            "expired_count": 2,
            "stock_turnover_rate": 2.5,
            "average_stock_value": 8333.33
        },
        "alerts": [
            {
                "type": "LOW_STOCK",
                "severity": "WARNING",
                "message": "Crocin is running low (5 units remaining)",
                "medicine_brand_id": "uuid",
                "medicine_brand_name": "Crocin",
                "current_quantity": 5,
                "threshold": 10
            }
        ],
        "charts": {
            "stock_value_trend": [
                {"date": "2026-01-01", "value": 1200000.00}
            ]
        }
    }}}
