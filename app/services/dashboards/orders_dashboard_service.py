"""
Orders Dashboard Service
Business logic for orders dashboard
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import DatabaseConnection
from app.repositories.dashboards.orders_dashboard_repository import OrdersDashboardRepository
from app.schemas.dashboards.orders_dashboard_schema import (
    OrdersDashboardResponse,
    OrdersKPIs,
    OrdersAlert,
    OrdersChartData,
    ChartDataPoint
)


class OrdersDashboardService:
    """Service for orders dashboard operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = OrdersDashboardRepository(session)
    
    async def get_dashboard(
        self,
        period: str = "month",
        include_charts: bool = True,
        trend_days: int = 30
    ) -> OrdersDashboardResponse:
        """
        Get complete orders dashboard data.
        
        Executes all queries in parallel for better performance.
        """
        # Get session factory for creating separate sessions for parallel queries
        session_factory = DatabaseConnection.get_session_factory()
        
        # Execute KPIs and alerts in parallel with separate sessions
        async def run_kpis():
            async with session_factory() as session:
                repo = OrdersDashboardRepository(session)
                return await repo.get_kpis(period)
        
        async def run_alerts():
            async with session_factory() as session:
                repo = OrdersDashboardRepository(session)
                return await repo.get_alerts()
        
        kpis_task = asyncio.create_task(run_kpis())
        alerts_task = asyncio.create_task(run_alerts())
        
        # Execute chart queries in parallel if needed
        chart_tasks = []
        if include_charts:
            async def run_orders_over_time():
                async with session_factory() as session:
                    repo = OrdersDashboardRepository(session)
                    return await repo.get_orders_over_time(trend_days)
            
            async def run_order_status_distribution():
                async with session_factory() as session:
                    repo = OrdersDashboardRepository(session)
                    return await repo.get_order_status_distribution()
            
            async def run_orders_by_source():
                async with session_factory() as session:
                    repo = OrdersDashboardRepository(session)
                    return await repo.get_orders_by_source()
            
            async def run_processing_time_analysis():
                async with session_factory() as session:
                    repo = OrdersDashboardRepository(session)
                    return await repo.get_processing_time_analysis()
            
            chart_tasks = [
                asyncio.create_task(run_orders_over_time()),
                asyncio.create_task(run_order_status_distribution()),
                asyncio.create_task(run_orders_by_source()),
                asyncio.create_task(run_processing_time_analysis()),
            ]
        
        # Wait for all tasks to complete
        kpis_data = await kpis_task
        alerts_data = await alerts_task
        
        # Build KPIs response
        kpis = OrdersKPIs(**kpis_data)
        
        # Build alerts response
        alerts = [OrdersAlert(**alert) for alert in alerts_data]
        
        # Build charts response
        charts = OrdersChartData()
        if include_charts and chart_tasks:
            chart_results = await asyncio.gather(*chart_tasks)
            
            charts.orders_over_time = [ChartDataPoint(**item) for item in chart_results[0]]
            charts.order_status_distribution = [ChartDataPoint(**item) for item in chart_results[1]]
            charts.orders_by_source = [ChartDataPoint(**item) for item in chart_results[2]]
            charts.processing_time_analysis = [ChartDataPoint(**item) for item in chart_results[3]]
        
        return OrdersDashboardResponse(
            kpis=kpis,
            alerts=alerts,
            charts=charts
        )
