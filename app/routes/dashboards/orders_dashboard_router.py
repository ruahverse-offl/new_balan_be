"""
Orders Dashboard Router
FastAPI routes for orders dashboard
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.utils.rbac import require_permission
from app.services.dashboards.orders_dashboard_service import OrdersDashboardService
from app.schemas.dashboards.orders_dashboard_schema import OrdersDashboardResponse

router = APIRouter(prefix="/api/v1/dashboards/orders", tags=["dashboards", "orders"])


@router.get("/", response_model=OrdersDashboardResponse)
async def get_orders_dashboard(
    period: str = Query(default="month", description="KPI period (today, week, month, quarter, year)"),
    include_charts: bool = Query(default=True, description="Include chart data"),
    trend_days: int = Query(default=30, ge=1, le=365, description="Days for trend charts"),
    _: UUID = Depends(require_permission("DASHBOARD_VIEW")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get orders dashboard data.

    Requires DASHBOARD_VIEW permission.

    Returns KPIs, alerts, and charts for order management.
    - **KPIs**: Total orders, pending, completed, processing time, fulfillment rate
    - **Alerts**: High pending orders, long processing times
    - **Charts**: Orders over time, status distribution, orders by source
    """
    service = OrdersDashboardService(db)
    dashboard = await service.get_dashboard(
        period=period,
        include_charts=include_charts,
        trend_days=trend_days
    )
    return dashboard
