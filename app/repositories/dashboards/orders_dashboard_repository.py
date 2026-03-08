"""
Orders Dashboard Repository
Database queries for orders dashboard aggregations
"""

from typing import Dict, List
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from app.db.models import Order


class OrdersDashboardRepository:
    """Repository for orders dashboard data aggregation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_kpis(self, period: str = "month") -> Dict:
        """Get orders KPIs."""
        today = date.today()
        
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
        
        # Approval pending
        approval_pending_query = select(
            func.count(Order.id).label("approval_pending")
        ).where(
            and_(
                Order.approval_status == "PENDING",
                Order.is_deleted == False
            )
        )
        
        approval_pending_result = await self.session.execute(approval_pending_query)
        approval_pending = approval_pending_result.scalar() or 0
        
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
        
        # Cancelled orders
        cancelled_orders_query = select(
            func.count(Order.id).label("cancelled_orders")
        ).where(
            and_(
                Order.order_status == "CANCELLED",
                Order.is_deleted == False
            )
        )
        
        cancelled_orders_result = await self.session.execute(cancelled_orders_query)
        cancelled_orders = cancelled_orders_result.scalar() or 0
        
        # Average processing time (simplified - time from creation to completion)
        processing_time_query = select(
            func.avg(
                func.extract('epoch', Order.updated_at - Order.created_at) / 3600
            ).label("avg_hours")
        ).where(
            and_(
                Order.order_status == "COMPLETED",
                Order.updated_at != None,
                Order.is_deleted == False
            )
        )
        
        processing_time_result = await self.session.execute(processing_time_query)
        avg_processing_time = processing_time_result.scalar()
        
        # Fulfillment rate
        fulfillment_rate = None
        if total_orders > 0:
            fulfillment_rate = (completed_orders / total_orders) * 100
        
        return {
            "total_orders": total_orders,
            "today_orders": today_orders,
            "month_orders": month_orders,
            "pending_orders": pending_orders,
            "approval_pending": approval_pending,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "average_processing_time_hours": Decimal(str(avg_processing_time)) if avg_processing_time else None,
            "fulfillment_rate": Decimal(str(fulfillment_rate)) if fulfillment_rate else None
        }
    
    async def get_alerts(self) -> List[Dict]:
        """Get orders alerts."""
        alerts = []
        kpis = await self.get_kpis()
        
        # High pending orders alert
        if kpis["pending_orders"] > 20:
            alerts.append({
                "type": "HIGH_PENDING",
                "severity": "WARNING",
                "message": f"{kpis['pending_orders']} orders are pending (above threshold of 20)",
                "pending_count": kpis["pending_orders"],
                "threshold": 20
            })
        
        return alerts
    
    async def get_orders_over_time(self, days: int = 30) -> List[Dict]:
        """Get orders over time."""
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
    
    async def get_orders_by_source(self) -> List[Dict]:
        """Get orders by source."""
        query = select(
            Order.order_source,
            func.count(Order.id).label("count")
        ).where(
            Order.is_deleted == False
        ).group_by(
            Order.order_source
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.order_source,
                "count": row.count
            }
            for row in result
        ]
    
    async def get_processing_time_analysis(self) -> List[Dict]:
        """Get processing time analysis by status."""
        query = select(
            Order.order_status,
            func.avg(
                func.extract('epoch', Order.updated_at - Order.created_at) / 3600
            ).label("average_time")
        ).where(
            and_(
                Order.updated_at != None,
                Order.is_deleted == False
            )
        ).group_by(
            Order.order_status
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.order_status,
                "average_time": Decimal(str(row.average_time)) if row.average_time else None
            }
            for row in result
        ]
