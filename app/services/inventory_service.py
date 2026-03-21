"""
Inventory: stock per medicine–brand offering, low-stock alerts vs INV_STOCK_THRESHOLD.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import (
    Inventory,
    InventoryAlert,
    MedicineBrandOffering,
    OrderItem,
    Brand,
    Medicine,
)

logger = logging.getLogger(__name__)


async def ensure_inventory_row(
    session: AsyncSession,
    offering_id: UUID,
    created_by: UUID,
    created_ip: str,
) -> Inventory:
    """Return existing row or insert one with stock 0."""
    q = await session.execute(
        select(Inventory).where(
            Inventory.medicine_brand_offering_id == offering_id,
            Inventory.is_deleted == False,  # noqa: E712
        )
    )
    row = q.scalar_one_or_none()
    if row:
        return row
    inv = Inventory(
        medicine_brand_offering_id=offering_id,
        stock_quantity=0,
        created_by=created_by,
        created_ip=created_ip,
    )
    session.add(inv)
    await session.flush()
    return inv


async def get_stock_map(session: AsyncSession, offering_ids: list[UUID]) -> dict[UUID, int]:
    """Return current stock for each offering id (missing rows count as 0)."""
    if not offering_ids:
        return {}
    q = await session.execute(
        select(Inventory.medicine_brand_offering_id, Inventory.stock_quantity).where(
            Inventory.medicine_brand_offering_id.in_(offering_ids),
            Inventory.is_deleted == False,  # noqa: E712
        )
    )
    m = {oid: qty for oid, qty in q.all()}
    return {oid: m.get(oid, 0) for oid in offering_ids}


async def sync_alert_for_offering(
    session: AsyncSession,
    offering_id: UUID,
    stock: int,
) -> None:
    """Delete alert if stock >= threshold; otherwise insert/update one row."""
    threshold = get_settings().INV_STOCK_THRESHOLD
    await session.execute(
        delete(InventoryAlert).where(InventoryAlert.medicine_brand_offering_id == offering_id)
    )
    if stock < threshold:
        session.add(
            InventoryAlert(
                medicine_brand_offering_id=offering_id,
                current_stock=stock,
                created_by=UUID("00000000-0000-0000-0000-000000000001"),
                created_ip="127.0.0.1",
            )
        )


async def validate_cart_stock(
    session: AsyncSession,
    offering_qty: list[tuple[UUID, int]],
    actor_id: UUID,
    ip: str,
) -> None:
    """
    Ensure each offering has enough stock. Raises ValueError with a user-facing message.

    ``offering_qty`` is [(medicine_brand_offering_id, quantity), ...].
    """
    from fastapi import HTTPException, status

    if not offering_qty:
        return
    for oid, qty in offering_qty:
        if qty < 1:
            continue
        await ensure_inventory_row(session, oid, actor_id, ip)
    stocks = await get_stock_map(session, [o for o, _ in offering_qty])
    for oid, qty in offering_qty:
        if qty < 1:
            continue
        have = stocks.get(oid, 0)
        if have < qty:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Insufficient stock for one or more items in your cart. "
                    f"Only {have} unit(s) available for a selected brand; you requested {qty}. "
                    "Reduce the quantity or try a different brand."
                ),
            )


async def decrease_stock_for_order(
    session: AsyncSession,
    order_id: UUID,
    updated_by: UUID,
    updated_ip: str,
) -> None:
    """
    Decrement inventory for each order line item (atomic per line).

    Call after payment is confirmed. Raises HTTPException 409 if any line cannot be fulfilled.
    """
    from fastapi import HTTPException, status

    r = await session.execute(
        select(OrderItem.medicine_brand_id, OrderItem.quantity).where(
            OrderItem.order_id == order_id,
            OrderItem.is_deleted == False,  # noqa: E712
        )
    )
    lines = list(r.all())
    if not lines:
        return

    for offering_id, qty in lines:
        if qty < 1:
            continue
        await ensure_inventory_row(session, offering_id, updated_by, updated_ip)
        stmt = (
            update(Inventory)
            .where(
                Inventory.medicine_brand_offering_id == offering_id,
                Inventory.is_deleted == False,  # noqa: E712
                Inventory.stock_quantity >= qty,
            )
            .values(
                stock_quantity=Inventory.stock_quantity - qty,
                updated_by=updated_by,
                updated_ip=updated_ip,
            )
        )
        res = await session.execute(stmt)
        if res.rowcount != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Inventory could not be updated for this order (insufficient stock).",
            )
        q2 = await session.execute(
            select(Inventory.stock_quantity).where(
                Inventory.medicine_brand_offering_id == offering_id,
                Inventory.is_deleted == False,  # noqa: E712
            )
        )
        new_stock = q2.scalar_one()
        await sync_alert_for_offering(session, offering_id, int(new_stock))
        logger.info(
            "Inventory decreased for offering %s by %s; new stock=%s",
            offering_id,
            qty,
            new_stock,
        )


async def set_stock_quantity(
    session: AsyncSession,
    offering_id: UUID,
    new_stock: int,
    updated_by: UUID,
    updated_ip: str,
) -> None:
    """Admin set absolute stock (or refill). Syncs alerts."""
    if new_stock < 0:
        raise ValueError("stock_quantity cannot be negative")
    await ensure_inventory_row(session, offering_id, updated_by, updated_ip)
    await session.execute(
        update(Inventory)
        .where(
            Inventory.medicine_brand_offering_id == offering_id,
            Inventory.is_deleted == False,  # noqa: E712
        )
        .values(
            stock_quantity=new_stock,
            updated_by=updated_by,
            updated_ip=updated_ip,
        )
    )
    await sync_alert_for_offering(session, offering_id, new_stock)


async def list_alerts_with_labels(
    session: AsyncSession,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    """Join alerts to medicine + brand names for admin UI."""
    stmt = (
        select(
            InventoryAlert.id,
            InventoryAlert.medicine_brand_offering_id,
            InventoryAlert.current_stock,
            InventoryAlert.created_at,
            Medicine.name,
            Brand.name,
        )
        .select_from(InventoryAlert)
        .join(
            MedicineBrandOffering,
            InventoryAlert.medicine_brand_offering_id == MedicineBrandOffering.id,
        )
        .join(Medicine, MedicineBrandOffering.medicine_id == Medicine.id)
        .join(Brand, MedicineBrandOffering.brand_id == Brand.id)
        .where(InventoryAlert.is_deleted == False)  # noqa: E712
        .order_by(InventoryAlert.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).all()
    out = []
    for (
        aid,
        oid,
        cur,
        created_at,
        med_name,
        brand_name,
    ) in rows:
        mn = med_name or ""
        bn = brand_name or ""
        out.append(
            {
                "id": str(aid),
                "medicine_brand_offering_id": str(oid),
                "medicine_name": mn,
                "brand_name": bn,
                "current_stock": int(cur),
                "message": (
                    f"{mn} ({bn}) has low stock: only {int(cur)} unit(s) available."
                ),
                "created_at": created_at.isoformat() if created_at else None,
            }
        )
    return out
