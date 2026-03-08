"""
Orders Dashboard Schema
Pydantic models for orders dashboard responses
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class OrdersKPIs(BaseModel):
    """Key Performance Indicators for orders dashboard."""
    
    total_orders: int = Field(..., description="Total orders (all-time)")
    today_orders: int = Field(..., description="Today's orders")
    month_orders: int = Field(..., description="This month's orders")
    pending_orders: int = Field(..., description="Pending orders count")
    approval_pending: int = Field(..., description="Orders awaiting approval")
    completed_orders: int = Field(..., description="Completed orders count")
    cancelled_orders: int = Field(..., description="Cancelled orders count")
    average_processing_time_hours: Optional[Decimal] = Field(None, description="Average processing time in hours")
    fulfillment_rate: Optional[Decimal] = Field(None, description="Order fulfillment rate (%)")


class OrdersAlert(BaseModel):
    """Alert for orders issues."""
    
    type: str = Field(..., description="Alert type: HIGH_PENDING, LONG_PROCESSING, HIGH_CANCELLATION")
    severity: str = Field(..., description="Alert severity: WARNING, CRITICAL")
    message: str = Field(..., description="Alert message")
    pending_count: Optional[int] = Field(None, description="Pending orders count")
    threshold: Optional[int] = Field(None, description="Threshold value")


class ChartDataPoint(BaseModel):
    """Data point for charts."""
    
    date: Optional[str] = Field(None, description="Date for time-series charts")
    label: Optional[str] = Field(None, description="Label for categorical charts")
    orders: Optional[int] = Field(None, description="Orders count")
    count: Optional[int] = Field(None, description="Count value")
    average_time: Optional[Decimal] = Field(None, description="Average processing time")


class OrdersChartData(BaseModel):
    """Chart data for orders dashboard."""
    
    orders_over_time: Optional[List[ChartDataPoint]] = Field(None, description="Orders over time")
    order_status_distribution: Optional[List[ChartDataPoint]] = Field(None, description="Order status distribution")
    orders_by_source: Optional[List[ChartDataPoint]] = Field(None, description="Orders by source")
    processing_time_analysis: Optional[List[ChartDataPoint]] = Field(None, description="Processing time analysis")


class OrdersDashboardResponse(BaseModel):
    """Complete orders dashboard response."""
    
    kpis: OrdersKPIs = Field(..., description="Key Performance Indicators")
    alerts: List[OrdersAlert] = Field(default_factory=list, description="Orders alerts")
    charts: OrdersChartData = Field(..., description="Chart data")
    
    model_config = {"json_schema_extra": {"example": {
        "kpis": {
            "total_orders": 5000,
            "today_orders": 50,
            "month_orders": 1500,
            "pending_orders": 25,
            "approval_pending": 10,
            "completed_orders": 4500,
            "cancelled_orders": 50,
            "average_processing_time_hours": 2.5,
            "fulfillment_rate": 90.0
        },
        "alerts": [],
        "charts": {}
    }}}
