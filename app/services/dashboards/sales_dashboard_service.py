"""
Sales Dashboard Service
Business logic for sales dashboard
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import DatabaseConnection
from app.repositories.dashboards.sales_dashboard_repository import SalesDashboardRepository
from app.schemas.dashboards.sales_dashboard_schema import (
    SalesDashboardResponse,
    SalesKPIs,
    SalesChartData,
    ChartDataPoint
)


class SalesDashboardService:
    """Service for sales dashboard operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = SalesDashboardRepository(session)
    
    async def get_dashboard(
        self,
        period: str = "30d",
        include_charts: bool = True,
        top_products_limit: int = 10
    ) -> SalesDashboardResponse:
        """
        Get complete sales dashboard data.
        
        Executes all queries in parallel for better performance.
        """
        # Parse period to days
        days = self._parse_period(period)
        
        # Get session factory for creating separate sessions for parallel queries
        session_factory = DatabaseConnection.get_session_factory()
        
        # Execute KPIs
        async def run_kpis():
            async with session_factory() as session:
                repo = SalesDashboardRepository(session)
                return await repo.get_kpis(days)
        
        kpis_task = asyncio.create_task(run_kpis())
        
        # Execute chart queries in parallel if needed
        chart_tasks = []
        if include_charts:
            async def run_top_products():
                async with session_factory() as session:
                    repo = SalesDashboardRepository(session)
                    return await repo.get_top_products(top_products_limit, days)
            
            async def run_sales_by_category():
                async with session_factory() as session:
                    repo = SalesDashboardRepository(session)
                    return await repo.get_sales_by_category(days)
            
            async def run_sales_trend():
                async with session_factory() as session:
                    repo = SalesDashboardRepository(session)
                    return await repo.get_sales_trend(days)
            
            async def run_sales_by_dosage_form():
                async with session_factory() as session:
                    repo = SalesDashboardRepository(session)
                    return await repo.get_sales_by_dosage_form(days)
            
            chart_tasks = [
                asyncio.create_task(run_top_products()),
                asyncio.create_task(run_sales_by_category()),
                asyncio.create_task(run_sales_trend()),
                asyncio.create_task(run_sales_by_dosage_form()),
            ]
        
        # Wait for all tasks to complete
        kpis_data = await kpis_task
        
        # Build KPIs response
        kpis = SalesKPIs(**kpis_data)
        
        # Build charts response
        charts = SalesChartData()
        if include_charts and chart_tasks:
            chart_results = await asyncio.gather(*chart_tasks)
            
            charts.top_products = [ChartDataPoint(**item) for item in chart_results[0]]
            charts.sales_by_category = [ChartDataPoint(**item) for item in chart_results[1]]
            charts.sales_trend = [ChartDataPoint(**item) for item in chart_results[2]]
            charts.sales_by_dosage_form = [ChartDataPoint(**item) for item in chart_results[3]]
        
        return SalesDashboardResponse(
            kpis=kpis,
            charts=charts
        )
    
    def _parse_period(self, period: str) -> int:
        """Parse period string to days."""
        if period.endswith("d"):
            return int(period[:-1])
        elif period.endswith("m"):
            return int(period[:-1]) * 30
        elif period.endswith("y"):
            return int(period[:-1]) * 365
        else:
            return 30  # default
