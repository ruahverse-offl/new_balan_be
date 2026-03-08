"""
Finance Dashboard Repository
Database queries for finance dashboard aggregations
"""

from typing import Dict, List, Optional
from datetime import date, timedelta, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, cast, Date, text

from app.db.models import Payment, Order


class FinanceDashboardRepository:
    """Repository for finance dashboard data aggregation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_kpis(self, period: str = "month") -> Dict:
        """Get finance KPIs."""
        today = date.today()
        
        # Calculate date ranges
        if period == "today":
            start_date = today
        elif period == "week":
            start_date = today - timedelta(days=7)
        elif period == "month":
            start_date = today.replace(day=1)
        elif period == "quarter":
            quarter_month = ((today.month - 1) // 3) * 3 + 1
            start_date = today.replace(month=quarter_month, day=1)
        elif period == "year":
            start_date = today.replace(month=1, day=1)
        else:
            start_date = None
        
        # Total revenue (all-time)
        total_revenue_query = select(
            func.coalesce(func.sum(Payment.amount), 0).label("total_revenue")
        ).where(
            and_(
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        )
        
        total_revenue_result = await self.session.execute(total_revenue_query)
        total_revenue = Decimal(str(total_revenue_result.scalar() or 0))
        
        # Today's revenue
        today_revenue_query = select(
            func.coalesce(func.sum(Payment.amount), 0).label("today_revenue")
        ).where(
            and_(
                func.date(Payment.created_at) == today,
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        )
        
        today_revenue_result = await self.session.execute(today_revenue_query)
        today_revenue = Decimal(str(today_revenue_result.scalar() or 0))
        
        # Month revenue
        month_revenue_query = select(
            func.coalesce(func.sum(Payment.amount), 0).label("month_revenue")
        ).where(
            and_(
                func.date(Payment.created_at) >= today.replace(day=1),
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        )
        
        month_revenue_result = await self.session.execute(month_revenue_query)
        month_revenue = Decimal(str(month_revenue_result.scalar() or 0))
        
        # Year revenue
        year_revenue_query = select(
            func.coalesce(func.sum(Payment.amount), 0).label("year_revenue")
        ).where(
            and_(
                func.date(Payment.created_at) >= today.replace(month=1, day=1),
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        )
        
        year_revenue_result = await self.session.execute(year_revenue_query)
        year_revenue = Decimal(str(year_revenue_result.scalar() or 0))
        
        # Total orders
        total_orders_query = select(
            func.count(Order.id).label("total_orders")
        ).where(
            Order.is_deleted == False
        )
        
        total_orders_result = await self.session.execute(total_orders_query)
        total_orders = total_orders_result.scalar() or 0
        
        # Today's orders
        today_orders_query = select(
            func.count(Order.id).label("today_orders")
        ).where(
            and_(
                func.date(Order.created_at) == today,
                Order.is_deleted == False
            )
        )
        
        today_orders_result = await self.session.execute(today_orders_query)
        today_orders = today_orders_result.scalar() or 0
        
        # Month orders
        month_orders_query = select(
            func.count(Order.id).label("month_orders")
        ).where(
            and_(
                func.date(Order.created_at) >= today.replace(day=1),
                Order.is_deleted == False
            )
        )
        
        month_orders_result = await self.session.execute(month_orders_query)
        month_orders = month_orders_result.scalar() or 0
        
        # Pending orders
        pending_orders_query = select(
            func.count(Order.id).label("pending_orders")
        ).where(
            and_(
                Order.order_status == "PENDING",
                Order.is_deleted == False
            )
        )
        
        pending_orders_result = await self.session.execute(pending_orders_query)
        pending_orders = pending_orders_result.scalar() or 0
        
        # Completed orders
        completed_orders_query = select(
            func.count(Order.id).label("completed_orders")
        ).where(
            and_(
                Order.order_status == "COMPLETED",
                Order.is_deleted == False
            )
        )
        
        completed_orders_result = await self.session.execute(completed_orders_query)
        completed_orders = completed_orders_result.scalar() or 0
        
        # Average order value
        aov = total_revenue / total_orders if total_orders > 0 else None
        
        # Outstanding payments
        outstanding_query = select(
            func.coalesce(func.sum(Payment.amount), 0).label("outstanding")
        ).where(
            and_(
                Payment.payment_status == "PENDING",
                Payment.is_deleted == False
            )
        )
        
        outstanding_result = await self.session.execute(outstanding_query)
        outstanding_payments = Decimal(str(outstanding_result.scalar() or 0))
        
        # Payment success rate
        total_payments_query = select(func.count(Payment.id)).where(
            Payment.is_deleted == False
        )
        total_payments_result = await self.session.execute(total_payments_query)
        total_payments = total_payments_result.scalar() or 0
        
        completed_payments_query = select(func.count(Payment.id)).where(
            and_(
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        )
        completed_payments_result = await self.session.execute(completed_payments_query)
        completed_payments = completed_payments_result.scalar() or 0
        
        payment_success_rate = (completed_payments / total_payments * 100) if total_payments > 0 else None
        
        # Revenue growth rate (month-over-month)
        last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_month_end = today.replace(day=1) - timedelta(days=1)
        
        last_month_revenue_query = select(
            func.coalesce(func.sum(Payment.amount), 0).label("last_month_revenue")
        ).where(
            and_(
                func.date(Payment.created_at) >= last_month_start,
                func.date(Payment.created_at) <= last_month_end,
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        )
        
        last_month_revenue_result = await self.session.execute(last_month_revenue_query)
        last_month_revenue = Decimal(str(last_month_revenue_result.scalar() or 0))
        
        revenue_growth_rate = None
        if last_month_revenue > 0:
            revenue_growth_rate = ((month_revenue - last_month_revenue) / last_month_revenue) * 100
        
        return {
            "total_revenue": total_revenue,
            "today_revenue": today_revenue,
            "month_revenue": month_revenue,
            "year_revenue": year_revenue,
            "total_orders": total_orders,
            "today_orders": today_orders,
            "month_orders": month_orders,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "average_order_value": aov,
            "revenue_growth_rate": revenue_growth_rate,
            "payment_success_rate": payment_success_rate,
            "outstanding_payments": outstanding_payments
        }
    
    async def get_alerts(self) -> List[Dict]:
        """Get finance alerts."""
        alerts = []
        kpis = await self.get_kpis()
        
        # Calculate average daily revenue (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        daily_subq = select(
            func.date(Payment.created_at).label("pay_date"),
            func.sum(Payment.amount).label("daily_revenue")
        ).where(
            and_(
                func.date(Payment.created_at) >= thirty_days_ago,
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        ).group_by(
            func.date(Payment.created_at)
        ).subquery()

        avg_daily_revenue_query = select(
            func.coalesce(func.avg(daily_subq.c.daily_revenue), 0).label("avg_daily_revenue")
        )

        avg_daily_revenue_result = await self.session.execute(avg_daily_revenue_query)
        avg_daily_revenue = Decimal(str(avg_daily_revenue_result.scalar() or 0))
        
        # Low revenue alert
        if avg_daily_revenue > 0 and kpis["today_revenue"] < (avg_daily_revenue * Decimal("0.7")):
            percentage_below = ((avg_daily_revenue - kpis["today_revenue"]) / avg_daily_revenue) * 100
            alerts.append({
                "type": "LOW_REVENUE",
                "severity": "WARNING",
                "message": f"Today's revenue is {percentage_below:.1f}% below average",
                "today_revenue": kpis["today_revenue"],
                "average_daily_revenue": avg_daily_revenue,
                "percentage_below": percentage_below
            })
        
        # High outstanding payments alert
        if kpis["month_revenue"] > 0:
            outstanding_percentage = (kpis["outstanding_payments"] / kpis["month_revenue"]) * 100
            if outstanding_percentage > 20:
                alerts.append({
                    "type": "HIGH_OUTSTANDING",
                    "severity": "WARNING",
                    "message": f"Outstanding payments exceed 20% of monthly revenue",
                    "outstanding_amount": kpis["outstanding_payments"],
                    "monthly_revenue": kpis["month_revenue"],
                    "percentage": outstanding_percentage
                })
        
        return alerts
    
    async def get_revenue_trend(self, days: int = 30, granularity: str = "daily") -> List[Dict]:
        """Get revenue trend over time."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        if granularity == "daily":
            date_trunc = func.date(Payment.created_at)
        elif granularity == "weekly":
            date_trunc = func.date_trunc('week', Payment.created_at)
        else:  # monthly
            date_trunc = func.date_trunc('month', Payment.created_at)
        
        query = select(
            date_trunc.label("date"),
            func.coalesce(func.sum(Payment.amount), 0).label("revenue")
        ).where(
            and_(
                func.date(Payment.created_at) >= start_date,
                func.date(Payment.created_at) <= end_date,
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        ).group_by(
            date_trunc
        ).order_by(
            date_trunc
        )
        
        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "revenue": Decimal(str(row.revenue))
            }
            for row in result
        ]
    
    async def get_orders_trend(self, days: int = 30) -> List[Dict]:
        """Get orders trend over time."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = select(
            func.date(Order.created_at).label("date"),
            func.count(Order.id).label("orders")
        ).where(
            and_(
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date,
                Order.is_deleted == False
            )
        ).group_by(
            func.date(Order.created_at)
        ).order_by(
            func.date(Order.created_at)
        )
        
        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "orders": row.orders
            }
            for row in result
        ]
    
    async def get_revenue_vs_orders(self, days: int = 30) -> List[Dict]:
        """Get revenue vs orders combined data."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get revenue data
        revenue_query = select(
            func.date(Payment.created_at).label("date"),
            func.coalesce(func.sum(Payment.amount), 0).label("revenue")
        ).where(
            and_(
                func.date(Payment.created_at) >= start_date,
                func.date(Payment.created_at) <= end_date,
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        ).group_by(
            func.date(Payment.created_at)
        )
        
        revenue_result = await self.session.execute(revenue_query)
        revenue_dict = {str(row.date): Decimal(str(row.revenue)) for row in revenue_result}
        
        # Get orders data
        orders_query = select(
            func.date(Order.created_at).label("date"),
            func.count(Order.id).label("orders")
        ).where(
            and_(
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date,
                Order.is_deleted == False
            )
        ).group_by(
            func.date(Order.created_at)
        )
        
        orders_result = await self.session.execute(orders_query)
        orders_dict = {str(row.date): row.orders for row in orders_result}
        
        # Combine data
        all_dates = set(list(revenue_dict.keys()) + list(orders_dict.keys()))
        return [
            {
                "date": d,
                "revenue": revenue_dict.get(d, Decimal("0")),
                "orders": orders_dict.get(d, 0)
            }
            for d in sorted(all_dates)
        ]
    
    async def get_payment_method_distribution(self) -> List[Dict]:
        """Get payment method distribution."""
        query = select(
            Payment.payment_method,
            func.count(Payment.id).label("count"),
            func.coalesce(func.sum(Payment.amount), 0).label("amount")
        ).where(
            Payment.is_deleted == False
        ).group_by(
            Payment.payment_method
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.payment_method,
                "count": row.count,
                "amount": Decimal(str(row.amount))
            }
            for row in result
        ]
    
    async def get_revenue_by_payment_method(self) -> List[Dict]:
        """Get revenue by payment method."""
        query = select(
            Payment.payment_method,
            func.coalesce(func.sum(Payment.amount), 0).label("revenue")
        ).where(
            and_(
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        ).group_by(
            Payment.payment_method
        ).order_by(
            func.sum(Payment.amount).desc()
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.payment_method,
                "revenue": Decimal(str(row.revenue))
            }
            for row in result
        ]
    
    async def get_daily_revenue_comparison(self) -> List[Dict]:
        """Get average revenue by day of week."""
        query = select(
            func.extract('dow', Payment.created_at).label("day_of_week"),
            func.avg(Payment.amount).label("average_revenue")
        ).where(
            and_(
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        ).group_by(
            func.extract('dow', Payment.created_at)
        )
        
        result = await self.session.execute(query)
        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        return [
            {
                "label": day_names[int(row.day_of_week)],
                "revenue": Decimal(str(row.average_revenue))
            }
            for row in result
        ]
    
    async def get_monthly_revenue_trend(self, months: int = 12) -> List[Dict]:
        """Get monthly revenue trend."""
        end_date = date.today()
        start_date = (end_date - timedelta(days=months * 30)).replace(day=1)
        
        # Create the date_trunc expression once and reuse it
        month_trunc = func.date_trunc('month', Payment.created_at)
        
        query = select(
            month_trunc.label("month"),
            func.coalesce(func.sum(Payment.amount), 0).label("revenue")
        ).where(
            and_(
                func.date(Payment.created_at) >= start_date,
                func.date(Payment.created_at) <= end_date,
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        ).group_by(
            month_trunc
        ).order_by(
            month_trunc
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": str(row.month)[:7],  # YYYY-MM format
                "revenue": Decimal(str(row.revenue))
            }
            for row in result
        ]
    
    async def get_order_status_distribution(self) -> List[Dict]:
        """Get order status distribution."""
        query = select(
            Order.order_status,
            func.count(Order.id).label("count")
        ).where(
            Order.is_deleted == False
        ).group_by(
            Order.order_status
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.order_status,
                "count": row.count
            }
            for row in result
        ]
    
    async def get_revenue_by_order_source(self) -> List[Dict]:
        """Get revenue by order source."""
        query = select(
            Order.order_source,
            func.coalesce(func.sum(Payment.amount), 0).label("revenue")
        ).select_from(
            Order
        ).join(
            Payment, Order.id == Payment.order_id
        ).where(
            and_(
                Payment.payment_status == "COMPLETED",
                Order.is_deleted == False,
                Payment.is_deleted == False
            )
        ).group_by(
            Order.order_source
        ).order_by(
            func.sum(Payment.amount).desc()
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.order_source,
                "revenue": Decimal(str(row.revenue))
            }
            for row in result
        ]
    
    async def get_aov_trend(self, days: int = 30) -> List[Dict]:
        """Get average order value trend."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        order_subq = select(
            Order.id.label("order_id"),
            func.date(Order.created_at).label("order_date"),
            func.coalesce(func.sum(Payment.amount), 0).label("order_revenue")
        ).select_from(
            Order
        ).join(
            Payment, Order.id == Payment.order_id
        ).where(
            and_(
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date,
                Payment.payment_status == "COMPLETED",
                Order.is_deleted == False,
                Payment.is_deleted == False
            )
        ).group_by(
            Order.id,
            func.date(Order.created_at)
        ).subquery()

        query = select(
            order_subq.c.order_date.label("date"),
            func.coalesce(func.avg(order_subq.c.order_revenue), 0).label("aov")
        ).group_by(
            order_subq.c.order_date
        ).order_by(
            order_subq.c.order_date
        )

        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "aov": Decimal(str(row.aov))
            }
            for row in result
        ]
    
    async def get_revenue_growth_rate(self, months: int = 12) -> List[Dict]:
        """Get revenue growth rate over months."""
        end_date = date.today()
        start_date = (end_date - timedelta(days=months * 30)).replace(day=1)
        
        # Create the date_trunc expression once and reuse it
        month_trunc = func.date_trunc('month', Payment.created_at)
        
        query = select(
            month_trunc.label("month"),
            func.coalesce(func.sum(Payment.amount), 0).label("revenue")
        ).where(
            and_(
                func.date(Payment.created_at) >= start_date,
                func.date(Payment.created_at) <= end_date,
                Payment.payment_status == "COMPLETED",
                Payment.is_deleted == False
            )
        ).group_by(
            month_trunc
        ).order_by(
            month_trunc
        )
        
        result = await self.session.execute(query)
        rows = list(result)
        
        # Calculate growth rate
        chart_data = []
        prev_revenue = None
        for row in rows:
            revenue = Decimal(str(row.revenue))
            growth_rate = None
            if prev_revenue and prev_revenue > 0:
                growth_rate = ((revenue - prev_revenue) / prev_revenue) * 100
            prev_revenue = revenue
            
            chart_data.append({
                "label": str(row.month)[:7],  # YYYY-MM format
                "growth_rate": growth_rate
            })
        
        return chart_data
    
    async def get_payment_status_breakdown(self, days: int = 30) -> List[Dict]:
        """Get payment status breakdown over time."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = select(
            func.date(Payment.created_at).label("date"),
            Payment.payment_status,
            func.count(Payment.id).label("count")
        ).where(
            and_(
                func.date(Payment.created_at) >= start_date,
                func.date(Payment.created_at) <= end_date,
                Payment.is_deleted == False
            )
        ).group_by(
            func.date(Payment.created_at),
            Payment.payment_status
        ).order_by(
            func.date(Payment.created_at),
            Payment.payment_status
        )
        
        result = await self.session.execute(query)
        
        # Group by date
        date_dict = {}
        for row in result:
            date_str = str(row.date)
            if date_str not in date_dict:
                date_dict[date_str] = {
                    "date": date_str,
                    "completed": 0,
                    "pending": 0,
                    "failed": 0,
                    "refunded": 0
                }
            
            status = row.payment_status.upper()
            if status == "COMPLETED":
                date_dict[date_str]["completed"] = row.count
            elif status == "PENDING":
                date_dict[date_str]["pending"] = row.count
            elif status == "FAILED":
                date_dict[date_str]["failed"] = row.count
            elif status == "REFUNDED":
                date_dict[date_str]["refunded"] = row.count
        
        return list(date_dict.values())
