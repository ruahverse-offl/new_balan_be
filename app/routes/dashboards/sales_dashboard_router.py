"""
Sales Dashboard Router
FastAPI routes for sales dashboard
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.utils.rbac import require_permission
from app.services.dashboards.sales_dashboard_service import SalesDashboardService
from app.schemas.dashboards.sales_dashboard_schema import SalesDashboardResponse

router = APIRouter(prefix="/api/v1/dashboards/sales", tags=["dashboards", "sales"])


@router.get("/", response_model=SalesDashboardResponse)
async def get_sales_dashboard(
    period: str = Query(default="30d", description="Time period (e.g., 30d, 3m, 1y)"),
    include_charts: bool = Query(default=True, description="Include chart data"),
    top_products_limit: int = Query(default=10, ge=1, le=50, description="Number of top products"),
    _: UUID = Depends(require_permission("DASHBOARD_VIEW")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sales dashboard data.

    Requires DASHBOARD_VIEW permission.

    Returns KPIs and charts for sales analysis.
    - **KPIs**: Total sales quantity, top selling product, growth rate, customer count
    - **Charts**: Top products, sales by category, sales trend, sales by dosage form
    """
    service = SalesDashboardService(db)
    dashboard = await service.get_dashboard(
        period=period,
        include_charts=include_charts,
        top_products_limit=top_products_limit
    )
    return dashboard
