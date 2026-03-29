"""
Delivery window enforcement helpers.

Slots are currently stored as a label string like "9:00 AM - 11:00 AM" (IST).
These helpers parse that format and determine whether orders can be placed now.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone, timedelta
from typing import Any, Iterable, List, Optional, Tuple


IST = timezone(timedelta(hours=5, minutes=30))


@dataclass(frozen=True)
class TimeRangeMinutes:
    start: int  # minutes from 00:00
    end: int


_SLOT_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*(AM|PM)\s*-\s*(\d{1,2}):(\d{2})\s*(AM|PM)\s*$", re.IGNORECASE)


def _to_minutes(h: int, m: int, ampm: str) -> int:
    h = h % 12
    if ampm.upper() == "PM":
        h += 12
    return h * 60 + m


def parse_slot_time_label(slot_time: str) -> Optional[TimeRangeMinutes]:
    """
    Parse "9:00 AM - 11:00 AM" into minutes range.
    Returns None if format is not recognized.
    """
    if not slot_time or not isinstance(slot_time, str):
        return None
    m = _SLOT_RE.match(slot_time)
    if not m:
        return None
    sh, sm, sampm, eh, em, eampm = m.groups()
    start = _to_minutes(int(sh), int(sm), sampm)
    end = _to_minutes(int(eh), int(em), eampm)
    return TimeRangeMinutes(start=start, end=end)


def now_ist_minutes(now: Optional[datetime] = None) -> int:
    dt = now or datetime.now(timezone.utc)
    ist = dt.astimezone(IST)
    return ist.hour * 60 + ist.minute


def slot_time_labels_from_delivery_slot_times_json(raw: Optional[str]) -> list[str]:
    """
    Parse delivery_settings.delivery_slot_times JSON (TEXT) into IST window labels.

    Accepts JSON array of strings or objects with slot_time / time and optional is_active.
    """
    if not raw or not isinstance(raw, str):
        return []
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    out: list[str] = []
    for item in parsed:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            if item.get("is_active") is False:
                continue
            label = item.get("slot_time") or item.get("time")
            if label and str(label).strip():
                out.append(str(label).strip())
    return out


def is_now_within_any_slot(slot_times: Iterable[str], now: Optional[datetime] = None) -> bool:
    now_min = now_ist_minutes(now)
    for label in slot_times:
        rng = parse_slot_time_label(label)
        if not rng:
            continue
        if now_min >= rng.start and now_min <= rng.end:
            return True
    return False


def slot_labels_from_parsed_items(parsed: Optional[Any]) -> List[str]:
    """Normalize API/DB list of slot objects (or JSON string) into IST window labels."""
    if not parsed:
        return []
    if isinstance(parsed, str):
        return slot_time_labels_from_delivery_slot_times_json(parsed)
    if not isinstance(parsed, list):
        return []
    out: List[str] = []
    for item in parsed:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            if item.get("is_active") is False:
                continue
            label = item.get("slot_time") or item.get("time")
            if label and str(label).strip():
                out.append(str(label).strip())
    return out


def _ist_date_and_minutes(now: Optional[datetime] = None) -> Tuple[date, int]:
    dt = now or datetime.now(timezone.utc)
    ist = dt.astimezone(IST)
    return ist.date(), ist.hour * 60 + ist.minute


def next_delivery_fulfillment_meta(
    slot_labels: List[str],
    now: Optional[datetime] = None,
) -> dict:
    """
    Decide which delivery window applies for an order placed *now* (IST).

    - If inside a configured window: that window today.
    - Else if a later window exists today: the next window today.
    - Else: first window on the next calendar day (IST).
    """
    today, now_min = _ist_date_and_minutes(now)
    parsed: List[Tuple[str, TimeRangeMinutes]] = []
    for label in slot_labels:
        rng = parse_slot_time_label(label)
        if rng:
            parsed.append((label, rng))
    if not parsed:
        return {
            "within_window": True,
            "slot_label": None,
            "date_iso": today.isoformat(),
            "customer_message": "Your order will be processed for delivery as per store timings.",
        }
    parsed.sort(key=lambda x: x[1].start)

    for label, rng in parsed:
        if rng.start <= now_min <= rng.end:
            return {
                "within_window": True,
                "slot_label": label,
                "date_iso": today.isoformat(),
                "customer_message": (
                    f"You are ordering during our delivery window ({label}). "
                    "We aim to deliver within this window when possible."
                ),
            }

    for label, rng in parsed:
        if now_min < rng.start:
            return {
                "within_window": False,
                "slot_label": label,
                "date_iso": today.isoformat(),
                "customer_message": (
                    f"Orders placed now are scheduled for today’s {label} delivery window."
                ),
            }

    tomorrow = today + timedelta(days=1)
    first_label = parsed[0][0]
    return {
        "within_window": False,
        "slot_label": first_label,
        "date_iso": tomorrow.isoformat(),
        "customer_message": (
            f"Today’s delivery windows have ended. This order is lined up for the next window: "
            f"{first_label} on {tomorrow.isoformat()} (IST)."
        ),
    }


def fulfillment_meta_to_order_note_line(meta: dict) -> str:
    if not meta.get("slot_label"):
        return "Delivery scheduling: as per store operations."
    return (
        f"Scheduled delivery window: {meta['slot_label']} "
        f"(IST calendar date {meta['date_iso']})."
    )


def delivery_schedule_public_meta(is_enabled: bool, parsed_slot_items: Optional[Any]) -> dict:
    """Fields merged into GET /delivery-settings for storefront / checkout / profile."""
    if not is_enabled:
        return {
            "delivery_on": False,
            "within_window": False,
            "slot_label": None,
            "fulfillment_date_iso": None,
            "customer_message": (
                "Home delivery is turned off. Please contact the store or visit in person."
            ),
        }
    labels = slot_labels_from_parsed_items(parsed_slot_items)
    if not labels:
        return {
            "delivery_on": True,
            "within_window": True,
            "slot_label": None,
            "fulfillment_date_iso": None,
            "customer_message": (
                "Orders are accepted online; delivery times follow store operations."
            ),
        }
    meta = next_delivery_fulfillment_meta(labels, now=None)
    return {
        "delivery_on": True,
        "within_window": meta["within_window"],
        "slot_label": meta["slot_label"],
        "fulfillment_date_iso": meta["date_iso"],
        "customer_message": meta["customer_message"],
    }

