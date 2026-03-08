"""
Finance Dashboard Service
Business logic for finance dashboard
"""

import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import DatabaseConnection
from app.repositories.dashboards.finance_dashboard_repository import FinanceDashboardRepository
from app.schemas.dashboards.finance_dashboard_schema import (
    FinanceDashboardResponse,
    FinanceKPIs,
    FinanceAlert,
    FinanceChartData,
    ChartDataPoint
)


class FinanceDashboardService:
    """Service for finance dashboard operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = FinanceDashboardRepository(session)
    
    async def get_dashboard(
        self,
        period: str = "month",
        trend_period: str = "30d",
        trend_granularity: str = "daily",
        include_charts: bool = True,
        monthly_trend_months: int = 12
    ) -> FinanceDashboardResponse:
        """
        Get complete finance dashboard data.
        
        Executes all queries in parallel for better performance.
        """
        # Parse trend period to days
        trend_days = self._parse_period(trend_period)
        
        # Get session factory for creating separate sessions for parallel queries
        session_factory = DatabaseConnection.get_session_factory()
        
        # Execute KPIs and alerts in parallel with separate sessions
        async def run_kpis():
            async with session_factory() as session:
                repo = FinanceDashboardRepository(session)
                return await repo.get_kpis(period)
        
        async def run_alerts():
            async with session_factory() as session:
                repo = FinanceDashboardRepository(session)
                return await repo.get_alerts()
        
        kpis_task = asyncio.create_task(run_kpis())
        alerts_task = asyncio.create_task(run_alerts())
        
        # Execute chart queries in parallel if needed
        chart_tasks = []
        if include_charts:
            async def run_revenue_trend():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_revenue_trend(trend_days, trend_granularity)
            
            async def run_orders_trend():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_orders_trend(trend_days)
            
            async def run_revenue_vs_orders():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_revenue_vs_orders(trend_days)
            
            async def run_payment_method_distribution():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_payment_method_distribution()
            
            async def run_revenue_by_payment_method():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_revenue_by_payment_method()
            
            async def run_daily_revenue_comparison():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_daily_revenue_comparison()
            
            async def run_monthly_revenue_trend():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_monthly_revenue_trend(monthly_trend_months)
            
            async def run_order_status_distribution():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_order_status_distribution()
            
            async def run_revenue_by_order_source():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_revenue_by_order_source()
            
            async def run_aov_trend():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_aov_trend(trend_days)
            
            async def run_revenue_growth_rate():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_revenue_growth_rate(monthly_trend_months)
            
            async def run_payment_status_breakdown():
                async with session_factory() as session:
                    repo = FinanceDashboardRepository(session)
                    return await repo.get_payment_status_breakdown(trend_days)
            
            chart_tasks = [
                asyncio.create_task(run_revenue_trend()),
                asyncio.create_task(run_orders_trend()),
                asyncio.create_task(run_revenue_vs_orders()),
                asyncio.create_task(run_payment_method_distribution()),
                asyncio.create_task(run_revenue_by_payment_method()),
                asyncio.create_task(run_daily_revenue_comparison()),
                asyncio.create_task(run_monthly_revenue_trend()),
                asyncio.create_task(run_order_status_distribution()),
                asyncio.create_task(run_revenue_by_order_source()),
                asyncio.create_task(run_aov_trend()),
                asyncio.create_task(run_revenue_growth_rate()),
                asyncio.create_task(run_payment_status_breakdown()),
            ]
        
        # Wait for all tasks to complete
        kpis_data = await kpis_task
        alerts_data = await alerts_task
        
        # Build KPIs response
        kpis = FinanceKPIs(**kpis_data)
        
        # Build alerts response
        alerts = [FinanceAlert(**alert) for alert in alerts_data]
        
        # Build charts response
        charts = FinanceChartData()
        if include_charts and chart_tasks:
            chart_results = await asyncio.gather(*chart_tasks)
            
            charts.revenue_trend = [ChartDataPoint(**item) for item in chart_results[0]]
            charts.orders_trend = [ChartDataPoint(**item) for item in chart_results[1]]
            charts.revenue_vs_orders = [ChartDataPoint(**item) for item in chart_results[2]]
            charts.payment_method_distribution = [ChartDataPoint(**item) for item in chart_results[3]]
            charts.revenue_by_payment_method = [ChartDataPoint(**item) for item in chart_results[4]]
            charts.daily_revenue_comparison = [ChartDataPoint(**item) for item in chart_results[5]]
            charts.monthly_revenue_trend = [ChartDataPoint(**item) for item in chart_results[6]]
            charts.order_status_distribution = [ChartDataPoint(**item) for item in chart_results[7]]
            charts.revenue_by_order_source = [ChartDataPoint(**item) for item in chart_results[8]]
            charts.aov_trend = [ChartDataPoint(**item) for item in chart_results[9]]
            charts.revenue_growth_rate = [ChartDataPoint(**item) for item in chart_results[10]]
            charts.payment_status_breakdown = [ChartDataPoint(**item) for item in chart_results[11]]
        
        return FinanceDashboardResponse(
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
