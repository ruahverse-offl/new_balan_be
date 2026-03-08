"""
Finance Dashboard Schema
Pydantic models for finance dashboard responses
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class FinanceKPIs(BaseModel):
    """Key Performance Indicators for finance dashboard."""
    
    total_revenue: Decimal = Field(..., description="Total revenue (all-time)")
    today_revenue: Decimal = Field(..., description="Today's revenue")
    month_revenue: Decimal = Field(..., description="This month's revenue")
    year_revenue: Decimal = Field(..., description="This year's revenue")
    total_orders: int = Field(..., description="Total orders (all-time)")
    today_orders: int = Field(..., description="Today's orders")
    month_orders: int = Field(..., description="This month's orders")
    pending_orders: int = Field(..., description="Pending orders count")
    completed_orders: int = Field(..., description="Completed orders count")
    average_order_value: Optional[Decimal] = Field(None, description="Average order value")
    revenue_growth_rate: Optional[Decimal] = Field(None, description="Revenue growth rate (%)")
    payment_success_rate: Optional[Decimal] = Field(None, description="Payment success rate (%)")
    outstanding_payments: Decimal = Field(..., description="Outstanding payments amount")


class FinanceAlert(BaseModel):
    """Alert for finance issues."""
    
    type: str = Field(..., description="Alert type: LOW_REVENUE, HIGH_OUTSTANDING, PAYMENT_FAILURE")
    severity: str = Field(..., description="Alert severity: WARNING, CRITICAL")
    message: str = Field(..., description="Alert message")
    today_revenue: Optional[Decimal] = Field(None, description="Today's revenue")
    average_daily_revenue: Optional[Decimal] = Field(None, description="Average daily revenue")
    percentage_below: Optional[Decimal] = Field(None, description="Percentage below average")
    outstanding_amount: Optional[Decimal] = Field(None, description="Outstanding amount")
    monthly_revenue: Optional[Decimal] = Field(None, description="Monthly revenue")
    percentage: Optional[Decimal] = Field(None, description="Percentage of monthly revenue")


class ChartDataPoint(BaseModel):
    """Data point for charts."""
    
    date: Optional[str] = Field(None, description="Date for time-series charts")
    label: Optional[str] = Field(None, description="Label for categorical charts")
    revenue: Optional[Decimal] = Field(None, description="Revenue value")
    orders: Optional[int] = Field(None, description="Orders count")
    amount: Optional[Decimal] = Field(None, description="Amount value")
    count: Optional[int] = Field(None, description="Count value")
    aov: Optional[Decimal] = Field(None, description="Average order value")
    growth_rate: Optional[Decimal] = Field(None, description="Growth rate")
    completed: Optional[int] = Field(None, description="Completed count")
    pending: Optional[int] = Field(None, description="Pending count")
    failed: Optional[int] = Field(None, description="Failed count")
    refunded: Optional[int] = Field(None, description="Refunded count")


class FinanceChartData(BaseModel):
    """Chart data for finance dashboard."""
    
    revenue_trend: Optional[List[ChartDataPoint]] = Field(None, description="Revenue over time")
    orders_trend: Optional[List[ChartDataPoint]] = Field(None, description="Orders over time")
    revenue_vs_orders: Optional[List[ChartDataPoint]] = Field(None, description="Revenue vs orders")
    payment_method_distribution: Optional[List[ChartDataPoint]] = Field(None, description="Payment method distribution")
    revenue_by_payment_method: Optional[List[ChartDataPoint]] = Field(None, description="Revenue by payment method")
    daily_revenue_comparison: Optional[List[ChartDataPoint]] = Field(None, description="Daily revenue comparison")
    monthly_revenue_trend: Optional[List[ChartDataPoint]] = Field(None, description="Monthly revenue trend")
    order_status_distribution: Optional[List[ChartDataPoint]] = Field(None, description="Order status distribution")
    revenue_by_order_source: Optional[List[ChartDataPoint]] = Field(None, description="Revenue by order source")
    aov_trend: Optional[List[ChartDataPoint]] = Field(None, description="Average order value trend")
    revenue_growth_rate: Optional[List[ChartDataPoint]] = Field(None, description="Revenue growth rate")
    payment_status_breakdown: Optional[List[ChartDataPoint]] = Field(None, description="Payment status breakdown")


class FinanceDashboardResponse(BaseModel):
    """Complete finance dashboard response."""
    
    kpis: FinanceKPIs = Field(..., description="Key Performance Indicators")
    alerts: List[FinanceAlert] = Field(default_factory=list, description="Finance alerts")
    charts: FinanceChartData = Field(..., description="Chart data")
    
    model_config = {"json_schema_extra": {"example": {
        "kpis": {
            "total_revenue": 5000000.00,
            "today_revenue": 50000.00,
            "month_revenue": 1500000.00,
            "year_revenue": 5000000.00,
            "total_orders": 5000,
            "today_orders": 50,
            "month_orders": 1500,
            "pending_orders": 25,
            "completed_orders": 4500,
            "average_order_value": 1111.11,
            "revenue_growth_rate": 15.5,
            "payment_success_rate": 98.5,
            "outstanding_payments": 25000.00
        },
        "alerts": [],
        "charts": {}
    }}}
