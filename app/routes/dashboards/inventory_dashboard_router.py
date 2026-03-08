"""
Inventory Dashboard Router
FastAPI routes for inventory dashboard
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.utils.rbac import require_permission
from app.services.dashboards.inventory_dashboard_service import InventoryDashboardService
from app.schemas.dashboards.inventory_dashboard_schema import InventoryDashboardResponse

router = APIRouter(prefix="/api/v1/dashboards/inventory", tags=["dashboards", "inventory"])


@router.get("/", response_model=InventoryDashboardResponse)
async def get_inventory_dashboard(
    period: str = Query(default="30d", description="Time period (e.g., 30d, 3m, 1y)"),
    include_charts: bool = Query(default=True, description="Include chart data"),
    low_stock_threshold: int = Query(default=10, ge=1, description="Low stock threshold"),
    expiry_days: int = Query(default=30, ge=1, description="Days ahead for expiring soon alerts"),
    top_products_limit: int = Query(default=10, ge=1, le=50, description="Number of top products"),
    expiry_months: int = Query(default=6, ge=1, le=24, description="Months for expiry timeline"),
    _: UUID = Depends(require_permission("DASHBOARD_VIEW")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get inventory dashboard data.

    Requires DASHBOARD_VIEW permission.

    Returns KPIs, alerts, and charts for inventory management.
    - **KPIs**: Stock value, quantities, low stock counts, expiry alerts
    - **Alerts**: Low stock, out of stock, expiring soon, expired items
    - **Charts**: Stock trends, category breakdown, top products, expiry timeline
    """
    service = InventoryDashboardService(db)
    dashboard = await service.get_dashboard(
        period=period,
        include_charts=include_charts,
        low_stock_threshold=low_stock_threshold,
        expiry_days=expiry_days,
        top_products_limit=top_products_limit,
        expiry_months=expiry_months
    )
    return dashboard
