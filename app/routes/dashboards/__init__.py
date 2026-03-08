"""
Dashboard Routes
FastAPI routes for dashboard endpoints
"""

from app.routes.dashboards.inventory_dashboard_router import router as inventory_router
from app.routes.dashboards.finance_dashboard_router import router as finance_router
from app.routes.dashboards.orders_dashboard_router import router as orders_router
from app.routes.dashboards.sales_dashboard_router import router as sales_router

__all__ = [
    "inventory_router",
    "finance_router",
    "orders_router",
    "sales_router",
]
