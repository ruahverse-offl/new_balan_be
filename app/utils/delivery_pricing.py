"""
Compute delivery fee from ``delivery_settings`` and cart subtotal.

Free delivery applies when subtotal is at least ``free_delivery_threshold`` (min) and
at most ``free_delivery_max_amount`` when that value is set and positive; otherwise
there is no upper bound.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models import DeliverySetting

# When no ``delivery_settings`` row exists, align with repository create defaults.
_DEFAULT_DELIVERY_FEE = Decimal("40")
_DEFAULT_FREE_MIN = Decimal("500")


def is_free_delivery(subtotal: Decimal, ds: Optional["DeliverySetting"]) -> bool:
    """Return True if this order amount qualifies for free delivery."""
    if ds is None:
        return subtotal >= _DEFAULT_FREE_MIN
    if ds.is_enabled is False:
        return False
    sub = Decimal(str(subtotal))
    dmin = Decimal(str(ds.free_delivery_threshold))
    if sub < dmin:
        return False
    raw_max = getattr(ds, "free_delivery_max_amount", None)
    if raw_max is None:
        return True
    dmax = Decimal(str(raw_max))
    if dmax <= 0:
        return True
    return sub <= dmax


def delivery_fee_for_subtotal(subtotal: Decimal, ds: Optional["DeliverySetting"]) -> Decimal:
    """Delivery charge for ``subtotal``; ``0`` when free delivery applies."""
    sub = Decimal(str(subtotal))
    if ds is None:
        return Decimal("0") if sub >= _DEFAULT_FREE_MIN else _DEFAULT_DELIVERY_FEE
    if ds.is_enabled is False:
        return Decimal("0")
    if is_free_delivery(sub, ds):
        return Decimal("0")
    return Decimal(str(ds.delivery_fee))
