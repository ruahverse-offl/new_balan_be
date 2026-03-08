"""
Dashboard Repositories
Repository classes for dashboard data aggregation
"""

from app.repositories.dashboards.inventory_dashboard_repository import InventoryDashboardRepository
from app.repositories.dashboards.finance_dashboard_repository import FinanceDashboardRepository
from app.repositories.dashboards.orders_dashboard_repository import OrdersDashboardRepository
from app.repositories.dashboards.sales_dashboard_repository import SalesDashboardRepository

__all__ = [
    "InventoryDashboardRepository",
    "FinanceDashboardRepository",
    "OrdersDashboardRepository",
    "SalesDashboardRepository",
]
