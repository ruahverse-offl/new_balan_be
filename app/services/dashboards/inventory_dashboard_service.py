"""
Inventory Dashboard Service
Business logic for inventory dashboard
"""

import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import DatabaseConnection
from app.repositories.dashboards.inventory_dashboard_repository import InventoryDashboardRepository
from app.schemas.dashboards.inventory_dashboard_schema import (
    InventoryDashboardResponse,
    InventoryKPIs,
    InventoryAlert,
    InventoryChartData,
    ChartDataPoint
)


class InventoryDashboardService:
    """Service for inventory dashboard operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = InventoryDashboardRepository(session)
    
    async def get_dashboard(
        self,
        period: str = "30d",
        include_charts: bool = True,
        low_stock_threshold: int = 10,
        expiry_days: int = 30,
        top_products_limit: int = 10,
        expiry_months: int = 6
    ) -> InventoryDashboardResponse:
        """
        Get complete inventory dashboard data.
        
        Executes all queries in parallel for better performance.
        """
        # Parse period to days
        days = self._parse_period(period)
        
        # Get session factory for creating separate sessions for parallel queries
        session_factory = DatabaseConnection.get_session_factory()
        
        # Create helper function to run query with its own session
        async def run_kpis():
            async with session_factory() as session:
                repo = InventoryDashboardRepository(session)
                result = await repo.get_kpis(low_stock_threshold, expiry_days)
                return result
        
        async def run_alerts():
            async with session_factory() as session:
                repo = InventoryDashboardRepository(session)
                result = await repo.get_alerts(low_stock_threshold, expiry_days)
                return result
        
        # Execute KPIs and alerts in parallel with separate sessions
        kpis_task = asyncio.create_task(run_kpis())
        alerts_task = asyncio.create_task(run_alerts())
        
        # Execute chart queries in parallel if needed
        chart_tasks = []
        if include_charts:
            async def run_stock_value_trend():
                async with session_factory() as session:
                    repo = InventoryDashboardRepository(session)
                    return await repo.get_stock_value_trend(days)
            
            async def run_stock_by_category():
                async with session_factory() as session:
                    repo = InventoryDashboardRepository(session)
                    return await repo.get_stock_by_category()
            
            async def run_top_products():
                async with session_factory() as session:
                    repo = InventoryDashboardRepository(session)
                    return await repo.get_top_products(top_products_limit)
            
            async def run_stock_distribution():
                async with session_factory() as session:
                    repo = InventoryDashboardRepository(session)
                    return await repo.get_stock_distribution(low_stock_threshold)
            
            async def run_expiry_timeline():
                async with session_factory() as session:
                    repo = InventoryDashboardRepository(session)
                    return await repo.get_expiry_timeline(expiry_months)
            
            async def run_stock_movement():
                async with session_factory() as session:
                    repo = InventoryDashboardRepository(session)
                    return await repo.get_stock_movement(days)
            
            async def run_stock_by_dosage_form():
                async with session_factory() as session:
                    repo = InventoryDashboardRepository(session)
                    return await repo.get_stock_by_dosage_form()
            
            chart_tasks = [
                asyncio.create_task(run_stock_value_trend()),
                asyncio.create_task(run_stock_by_category()),
                asyncio.create_task(run_top_products()),
                asyncio.create_task(run_stock_distribution()),
                asyncio.create_task(run_expiry_timeline()),
                asyncio.create_task(run_stock_movement()),
                asyncio.create_task(run_stock_by_dosage_form()),
            ]
        
        # Wait for all tasks to complete
        kpis_data = await kpis_task
        alerts_data = await alerts_task
        
        # Build KPIs response
        kpis = InventoryKPIs(**kpis_data)
        
        # Build alerts response
        alerts = [InventoryAlert(**alert) for alert in alerts_data]
        
        # Build charts response
        charts = InventoryChartData()
        if include_charts and chart_tasks:
            chart_results = await asyncio.gather(*chart_tasks)
            
            charts.stock_value_trend = [ChartDataPoint(**item) for item in chart_results[0]]
            charts.stock_by_category = [ChartDataPoint(**item) for item in chart_results[1]]
            charts.top_products = [ChartDataPoint(**item) for item in chart_results[2]]
            charts.stock_distribution = [ChartDataPoint(**item) for item in chart_results[3]]
            charts.expiry_timeline = [ChartDataPoint(**item) for item in chart_results[4]]
            charts.stock_movement = [ChartDataPoint(**item) for item in chart_results[5]]
            charts.stock_by_dosage_form = [ChartDataPoint(**item) for item in chart_results[6]]
        
        return InventoryDashboardResponse(
            kpis=kpis,
            alerts=alerts,
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
