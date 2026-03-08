"""
Sales Dashboard Schema
Pydantic models for sales dashboard responses
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class SalesKPIs(BaseModel):
    """Key Performance Indicators for sales dashboard."""
    
    total_sales_quantity: int = Field(..., description="Total sales quantity")
    top_selling_product: Optional[str] = Field(None, description="Top selling product name")
    sales_growth_rate: Optional[Decimal] = Field(None, description="Sales growth rate (%)")
    average_sales_per_day: Optional[Decimal] = Field(None, description="Average sales per day")
    customer_count: int = Field(..., description="Unique customer count")


class ChartDataPoint(BaseModel):
    """Data point for charts."""
    
    date: Optional[str] = Field(None, description="Date for time-series charts")
    label: Optional[str] = Field(None, description="Label for categorical charts")
    quantity: Optional[int] = Field(None, description="Sales quantity")
    revenue: Optional[Decimal] = Field(None, description="Sales revenue")
    count: Optional[int] = Field(None, description="Count value")


class SalesChartData(BaseModel):
    """Chart data for sales dashboard."""
    
    top_products: Optional[List[ChartDataPoint]] = Field(None, description="Top selling products")
    sales_by_category: Optional[List[ChartDataPoint]] = Field(None, description="Sales by category")
    sales_trend: Optional[List[ChartDataPoint]] = Field(None, description="Sales trend")
    sales_by_dosage_form: Optional[List[ChartDataPoint]] = Field(None, description="Sales by dosage form")


class SalesDashboardResponse(BaseModel):
    """Complete sales dashboard response."""
    
    kpis: SalesKPIs = Field(..., description="Key Performance Indicators")
    charts: SalesChartData = Field(..., description="Chart data")
    
    model_config = {"json_schema_extra": {"example": {
        "kpis": {
            "total_sales_quantity": 10000,
            "top_selling_product": "Crocin",
            "sales_growth_rate": 12.5,
            "average_sales_per_day": 333.33,
            "customer_count": 500
        },
        "charts": {}
    }}}
