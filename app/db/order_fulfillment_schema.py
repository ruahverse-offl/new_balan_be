"""
Idempotent PostgreSQL patches for T_orders (delivery assignment, cancel/return).

SQLAlchemy create_all() does not add new columns to existing tables; these statements
align older databases with app.db.models.Order.
"""

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import text

_ORDER_FULFILLMENT_STATEMENTS = (
    """
    ALTER TABLE "T_orders"
        ADD COLUMN IF NOT EXISTS delivery_assigned_user_id UUID REFERENCES "M_users"(id),
        ADD COLUMN IF NOT EXISTS cancellation_reason TEXT,
        ADD COLUMN IF NOT EXISTS cancelled_by_user_id UUID REFERENCES "M_users"(id),
        ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS return_reason TEXT
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_t_orders_delivery_assigned_user_id
        ON "T_orders"(delivery_assigned_user_id)
        WHERE delivery_assigned_user_id IS NOT NULL AND is_deleted = false
    """,
    """UPDATE "T_orders" SET order_status = 'ORDER_RECEIVED' WHERE order_status = 'CONFIRMED'""",
    """UPDATE "T_orders" SET order_status = 'CANCELLED_BY_STAFF' WHERE order_status = 'CANCELLED'""",
    """UPDATE "T_orders" SET order_status = 'DELIVERED' WHERE order_status = 'COMPLETED'""",
    """UPDATE "T_orders" SET order_status = 'ORDER_PROCESSING' WHERE order_status = 'PROCESSING'""",
    """UPDATE "T_orders" SET order_status = 'OUT_FOR_DELIVERY' WHERE order_status = 'SHIPPED'""",
)


async def apply_order_fulfillment_schema(conn: AsyncConnection) -> None:
    for raw in _ORDER_FULFILLMENT_STATEMENTS:
        stmt = raw.strip()
        if stmt:
            await conn.execute(text(stmt))
