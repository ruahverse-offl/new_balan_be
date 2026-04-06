"""
Order fulfillment lifecycle: staff queue, delivery assignment, and terminal outcomes.

Legacy values (PENDING, CONFIRMED, CANCELLED, COMPLETED) are normalized for transition rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional, Set, Tuple

# Payment not completed (Razorpay / checkout created, not verified yet)
PAYMENT_PENDING = "PENDING"

# Staff queue (paid or placed for fulfillment)
ORDER_RECEIVED = "ORDER_RECEIVED"
ORDER_TAKEN = "ORDER_TAKEN"
ORDER_PROCESSING = "ORDER_PROCESSING"
DELIVERY_ASSIGNED = "DELIVERY_ASSIGNED"
PARCEL_TAKEN = "PARCEL_TAKEN"
OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
DELIVERED = "DELIVERED"

CANCELLED_BY_STAFF = "CANCELLED_BY_STAFF"
DELIVERY_RETURNED = "DELIVERY_RETURNED"

# Payment / admin (unchanged from existing flows)
REFUND_INITIATED = "REFUND_INITIATED"
REFUNDED = "REFUNDED"

ALL_STATUSES: FrozenSet[str] = frozenset(
    {
        PAYMENT_PENDING,
        ORDER_RECEIVED,
        ORDER_TAKEN,
        ORDER_PROCESSING,
        DELIVERY_ASSIGNED,
        PARCEL_TAKEN,
        OUT_FOR_DELIVERY,
        DELIVERED,
        CANCELLED_BY_STAFF,
        DELIVERY_RETURNED,
        REFUND_INITIATED,
        REFUNDED,
    }
)

STAFF_TRANSITIONS: dict[str, Set[str]] = {
    PAYMENT_PENDING: {CANCELLED_BY_STAFF},
    ORDER_RECEIVED: {ORDER_TAKEN, CANCELLED_BY_STAFF},
    ORDER_TAKEN: {ORDER_PROCESSING, CANCELLED_BY_STAFF},
    ORDER_PROCESSING: {DELIVERY_ASSIGNED, CANCELLED_BY_STAFF},
    DELIVERY_ASSIGNED: {CANCELLED_BY_STAFF},
    PARCEL_TAKEN: {CANCELLED_BY_STAFF},
    OUT_FOR_DELIVERY: {CANCELLED_BY_STAFF},
}

DELIVERY_TRANSITIONS: dict[str, Set[str]] = {
    DELIVERY_ASSIGNED: {PARCEL_TAKEN},
    PARCEL_TAKEN: {OUT_FOR_DELIVERY},
    OUT_FOR_DELIVERY: {DELIVERED, DELIVERY_RETURNED},
}

TERMINAL_STATUSES: FrozenSet[str] = frozenset(
    {DELIVERED, CANCELLED_BY_STAFF, DELIVERY_RETURNED, REFUND_INITIATED, REFUNDED}
)


def normalize_order_status(raw: Optional[str]) -> str:
    """Map legacy DB values to canonical statuses used by transition rules."""
    if not raw:
        return PAYMENT_PENDING
    r = raw.strip().upper()
    if r == "CONFIRMED":
        return ORDER_RECEIVED
    if r == "CANCELLED":
        return CANCELLED_BY_STAFF
    if r == "COMPLETED":
        return DELIVERED
    if r == "SHIPPED":
        return OUT_FOR_DELIVERY
    if r == "PROCESSING":
        return ORDER_PROCESSING
    return r


def is_terminal_status(raw: Optional[str]) -> bool:
    return normalize_order_status(raw) in TERMINAL_STATUSES or raw in TERMINAL_STATUSES


@dataclass
class TransitionCheck:
    ok: bool
    error: Optional[str] = None


def validate_status_transition(
    current_raw: str,
    new_status: str,
    *,
    actor_is_staff: bool,
    actor_is_assigned_delivery: bool,
) -> TransitionCheck:
    """
    Validate order_status change. Refund statuses are set only by payment routes, not PATCH.
    """
    current = normalize_order_status(current_raw)
    new_s = (new_status or "").strip().upper()

    if new_s in (REFUND_INITIATED, REFUNDED):
        return TransitionCheck(False, "Refund statuses cannot be set via order update.")

    if new_s not in ALL_STATUSES:
        return TransitionCheck(False, f"Unknown order_status: {new_s}.")

    if current == new_s and new_s != DELIVERY_ASSIGNED:
        return TransitionCheck(True)

    if is_terminal_status(current_raw):
        return TransitionCheck(False, f"Cannot change status from terminal state {current_raw}.")

    if new_s == current:
        return TransitionCheck(True)

    allowed_staff = STAFF_TRANSITIONS.get(current, set())
    allowed_delivery = DELIVERY_TRANSITIONS.get(current, set())

    if new_s in allowed_staff:
        if not actor_is_staff:
            return TransitionCheck(False, f"Transition to {new_s} requires staff (ORDER_UPDATE) permission.")
        return TransitionCheck(True)

    if new_s in allowed_delivery:
        if not actor_is_assigned_delivery and not actor_is_staff:
            return TransitionCheck(
                False,
                f"Transition to {new_s} requires being the assigned delivery user or staff.",
            )
        return TransitionCheck(True)

    return TransitionCheck(
        False,
        f"Invalid transition from {current} to {new_s}.",
    )


def delivery_agent_must_be_assigned_for_transition(from_raw: str, to_status: str) -> bool:
    """Parcel/delivery steps require an assigned agent (except staff override)."""
    current = normalize_order_status(from_raw)
    to_s = (to_status or "").strip().upper()
    if to_s not in DELIVERY_TRANSITIONS.get(current, set()):
        return False
    return True
