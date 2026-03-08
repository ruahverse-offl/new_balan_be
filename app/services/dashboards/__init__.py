"""
Dashboard Services
Service classes for dashboard business logic
"""

from app.services.dashboards.inventory_dashboard_service import InventoryDashboardService
from app.services.dashboards.finance_dashboard_service import FinanceDashboardService
from app.services.dashboards.orders_dashboard_service import OrdersDashboardService
from app.services.dashboards.sales_dashboard_service import SalesDashboardService

__all__ = [
    "InventoryDashboardService",
    "FinanceDashboardService",
    "OrdersDashboardService",
    "SalesDashboardService",
]
