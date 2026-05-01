"""
Orders Repository
Data access layer for orders
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy import select, func
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
