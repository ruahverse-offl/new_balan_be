"""
Pydantic models for KPI summary API responses.
"""

from decimal import Decimal

from pydantic import BaseModel, Field


class KpiSummaryResponse(BaseModel):
    """Aggregated KPIs for the admin statistics view."""

    total_orders: int = Field(..., description="Count of non-deleted orders")
    total_medicines: int = Field(..., description="Count of non-deleted medicine records")
    total_sales: Decimal = Field(
        ...,
        description="Sum of order final_amount values (excludes cancelled orders)",
    )
