"""
Dashboard Schemas
Pydantic models for dashboard responses
"""

from app.schemas.dashboards.inventory_dashboard_schema import (
    InventoryDashboardResponse,
    InventoryKPIs,
    InventoryAlert,
    InventoryChartData
)
from app.schemas.dashboards.finance_dashboard_schema import (
    FinanceDashboardResponse,
    FinanceKPIs,
    FinanceAlert,
    FinanceChartData
)
from app.schemas.dashboards.orders_dashboard_schema import (
    OrdersDashboardResponse,
    OrdersKPIs,
    OrdersAlert,
    OrdersChartData
)
from app.schemas.dashboards.sales_dashboard_schema import (
    SalesDashboardResponse,
    SalesKPIs,
    SalesChartData
)

__all__ = [
    "InventoryDashboardResponse",
    "InventoryKPIs",
    "InventoryAlert",
    "InventoryChartData",
    "FinanceDashboardResponse",
    "FinanceKPIs",
    "FinanceAlert",
    "FinanceChartData",
    "OrdersDashboardResponse",
    "OrdersKPIs",
    "OrdersAlert",
    "OrdersChartData",
    "SalesDashboardResponse",
    "SalesKPIs",
    "SalesChartData",
]
