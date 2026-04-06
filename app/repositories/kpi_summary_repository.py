"""
KPI summary repository
Lightweight aggregates for admin overview (orders, medicines, sales revenue).
"""

from decimal import Decimal
from typing import Dict

from sqlalchemy import func, select, and_, not_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Medicine, Order


class KpiSummaryRepository:
    """Repository for global KPI counts and totals."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self) -> Dict[str, object]:
        """
        Return total non-deleted order count, medicine count, and total sales (sum of order final_amount).

        Returns:
            Dict with keys: total_orders (int), total_medicines (int), total_sales (Decimal).
        """
        total_orders_q = select(func.count(Order.id)).where(Order.is_deleted == False)  # noqa: E712
        total_orders = (await self.session.execute(total_orders_q)).scalar() or 0

        total_medicines_q = select(func.count(Medicine.id)).where(Medicine.is_deleted == False)  # noqa: E712
        total_medicines = (await self.session.execute(total_medicines_q)).scalar() or 0

        # Total sales: exclude cancelled, staff-cancelled, undelivered returns, refunds
        excluded_statuses = (
            "CANCELLED",
            "CANCELLED_BY_STAFF",
            "DELIVERY_RETURNED",
            "REFUND_INITIATED",
            "REFUNDED",
        )
        total_sales_q = select(func.coalesce(func.sum(Order.final_amount), 0)).where(
            and_(
                Order.is_deleted == False,  # noqa: E712
                not_(Order.order_status.in_(excluded_statuses)),
            )
        )
        total_sales_raw = (await self.session.execute(total_sales_q)).scalar() or 0
        total_sales = Decimal(str(total_sales_raw))

        return {
            "total_orders": int(total_orders),
            "total_medicines": int(total_medicines),
            "total_sales": total_sales,
        }
