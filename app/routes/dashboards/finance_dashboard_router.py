"""
Finance Dashboard Router
FastAPI routes for finance dashboard
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.utils.rbac import require_permission
from app.services.dashboards.finance_dashboard_service import FinanceDashboardService
from app.schemas.dashboards.finance_dashboard_schema import FinanceDashboardResponse

router = APIRouter(prefix="/api/v1/dashboards/finance", tags=["dashboards", "finance"])


@router.get("/", response_model=FinanceDashboardResponse)
async def get_finance_dashboard(
    period: str = Query(default="month", description="KPI period (today, week, month, quarter, year)"),
    trend_period: str = Query(default="30d", description="Trend period (e.g., 30d, 3m, 1y)"),
    trend_granularity: str = Query(default="daily", pattern="^(daily|weekly|monthly)$", description="Trend granularity"),
    include_charts: bool = Query(default=True, description="Include chart data"),
    monthly_trend_months: int = Query(default=12, ge=1, le=36, description="Months for monthly trend"),
    _: UUID = Depends(require_permission("DASHBOARD_VIEW")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get finance dashboard data.

    Requires DASHBOARD_VIEW permission.

    Returns KPIs, alerts, and charts for financial management.
    - **KPIs**: Revenue (total, today, month, year), orders, AOV, growth rate
    - **Alerts**: Low revenue, high outstanding payments, payment failures
    - **Charts**: Revenue trends, payment methods, order status, growth rates
    """
    service = FinanceDashboardService(db)
    dashboard = await service.get_dashboard(
        period=period,
        trend_period=trend_period,
        trend_granularity=trend_granularity,
        include_charts=include_charts,
        monthly_trend_months=monthly_trend_months
    )
    return dashboard
