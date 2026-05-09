"""
Orders Repository
Data access layer for orders
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy import select, func, cast, case, Date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base_repository import BaseRepository
from app.db.models import Order
from app.domain import order_lifecycle as lc
from app.utils.pagination import calculate_pagination
from app.utils.search import apply_search_filter
from app.utils.sort import apply_sort

# GET /api/v1/orders?delivery_list_scope=… (delivery-assigned users only)
_DELIVERY_LIST_ACTIVE_STATUSES: Tuple[str, ...] = (
    lc.DELIVERY_ASSIGNED,
    lc.PARCEL_TAKEN,
    lc.OUT_FOR_DELIVERY,
    "SHIPPED",  # legacy → OUT_FOR_DELIVERY
)
_DELIVERY_LIST_HISTORY_STATUSES: Tuple[str, ...] = (
    lc.DELIVERED,
    lc.DELIVERY_RETURNED,
    "COMPLETED",  # legacy → DELIVERED
)

# Staff "active" = everything not yet terminal; "history" = completed / cancelled / refunded
_STAFF_HISTORY_STATUSES: Tuple[str, ...] = (
    lc.DELIVERED,
    lc.DELIVERY_RETURNED,
    lc.CANCELLED_BY_STAFF,
    lc.REFUNDED,
    lc.PAYMENT_CANCELLED,
    "COMPLETED",  # legacy
    "CANCELLED",  # legacy
)


class OrdersRepository(BaseRepository[Order]):
    """Repository for orders table."""

    def __init__(self, session: AsyncSession):
        super().__init__(Order, session)

    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for orders."""
        return ["order_status", "customer_phone", "order_reference", "customer_name"]

    async def get_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        additional_filters: Optional[Dict[str, Any]] = None,
        *,
        delivery_agent_status_scope: Optional[str] = None,
        staff_scope: Optional[str] = None,
        order_date: Optional[str] = None,
    ) -> tuple[List[Order], Dict[str, Any]]:
        """
        Paginated orders list; extends base with optional delivery-agent tab filter.

        ``delivery_agent_status_scope``:
        - ``active``: assigned orders still in the courier pipeline.
        - ``history``: delivered or returned to store (customer refused / not accepted).
        """
        query = select(self.model).where(self.model.is_deleted == False)  # noqa: E712

        if additional_filters:
            for field_name, field_value in additional_filters.items():
                if hasattr(self.model, field_name) and field_value is not None:
                    query = query.where(getattr(self.model, field_name) == field_value)

        if delivery_agent_status_scope == "active":
            query = query.where(self.model.order_status.in_(_DELIVERY_LIST_ACTIVE_STATUSES))
        elif delivery_agent_status_scope == "history":
            query = query.where(self.model.order_status.in_(_DELIVERY_LIST_HISTORY_STATUSES))

        if staff_scope == "active":
            query = query.where(~self.model.order_status.in_(_STAFF_HISTORY_STATUSES))
        elif staff_scope == "history":
            query = query.where(self.model.order_status.in_(_STAFF_HISTORY_STATUSES))

        if order_date:
            query = query.where(cast(self.model.created_at, Date) == order_date)

        if search:
            searchable_fields = self._get_searchable_fields()
            query = apply_search_filter(query, self.model, search, searchable_fields)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = apply_sort(query, self.model, sort_by, sort_order)
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        records = result.scalars().all()
        pagination = calculate_pagination(total, limit, offset)
        return list(records), pagination

    async def get_sales_summary(self) -> dict:
        """Aggregate final_amount by terminal status for the sales KPI strip.

        *net_revenue* (owner-facing): delivered minus returns and refunds only — money
        notionally realized then reversed. Cancelled orders are shown separately; they
        often never became collected revenue, so subtracting them from the headline
        misstates \"how much sale value we kept after fulfilment reversals\".

        *net_sales* (legacy): also subtracts cancelled order values (can go deeply
        negative when cancellations are large vs delivered).
        """
        stmt = select(
            func.coalesce(func.sum(case(
                (self.model.order_status.in_([lc.DELIVERED, "COMPLETED"]), self.model.final_amount),
                else_=Decimal("0"),
            )), Decimal("0")).label("delivered"),
            func.coalesce(func.sum(case(
                (self.model.order_status == lc.DELIVERY_RETURNED, self.model.final_amount),
                else_=Decimal("0"),
            )), Decimal("0")).label("returned"),
            func.coalesce(func.sum(case(
                (self.model.order_status.in_([lc.CANCELLED_BY_STAFF, lc.CANCELLED_BY_CUSTOMER, "CANCELLED"]), self.model.final_amount),
                else_=Decimal("0"),
            )), Decimal("0")).label("cancelled"),
            func.coalesce(func.sum(case(
                (
                    self.model.order_status.in_([lc.REFUNDED, lc.REFUND_INITIATED]),
                    self.model.final_amount,
                ),
                else_=Decimal("0"),
            )), Decimal("0")).label("refunded"),
        ).where(self.model.is_deleted == False)  # noqa: E712
        row = (await self.session.execute(stmt)).one()
        delivered = row.delivered or Decimal("0")
        returned = row.returned or Decimal("0")
        cancelled = row.cancelled or Decimal("0")
        refunded = row.refunded or Decimal("0")
        net_revenue = delivered - cancelled - returned - refunded
        return {
            "delivered_amount": delivered,
            "returned_amount": returned,
            "cancelled_amount": cancelled,
            "refunded_amount": refunded,
            "net_revenue": net_revenue,
            "net_sales": net_revenue,
        }
