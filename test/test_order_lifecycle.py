"""Unit tests for order lifecycle rules (no HTTP)."""

import pytest

from app.domain import order_lifecycle as lc


def test_normalize_confirmed_to_received():
    assert lc.normalize_order_status("CONFIRMED") == lc.ORDER_RECEIVED


def test_staff_transition_received_to_taken():
    r = lc.validate_status_transition(
        "ORDER_RECEIVED",
        lc.ORDER_TAKEN,
        actor_is_staff=True,
        actor_is_assigned_delivery=False,
    )
    assert r.ok


def test_delivery_transition_requires_agent_or_staff():
    r = lc.validate_status_transition(
        "DELIVERY_ASSIGNED",
        lc.PARCEL_TAKEN,
        actor_is_staff=False,
        actor_is_assigned_delivery=False,
    )
    assert not r.ok

    r2 = lc.validate_status_transition(
        "DELIVERY_ASSIGNED",
        lc.PARCEL_TAKEN,
        actor_is_staff=False,
        actor_is_assigned_delivery=True,
    )
    assert r2.ok


def test_cancel_from_pending_staff_only():
    r = lc.validate_status_transition(
        "PENDING",
        lc.CANCELLED_BY_STAFF,
        actor_is_staff=False,
        actor_is_assigned_delivery=False,
    )
    assert not r.ok
