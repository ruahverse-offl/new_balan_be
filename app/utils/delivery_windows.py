"""
Delivery window enforcement helpers.

Slots are currently stored as a label string like "9:00 AM - 11:00 AM" (IST).
These helpers parse that format and determine whether orders can be placed now.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Iterable, Optional


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


def is_now_within_any_slot(slot_times: Iterable[str], now: Optional[datetime] = None) -> bool:
    now_min = now_ist_minutes(now)
    for label in slot_times:
        rng = parse_slot_time_label(label)
        if not rng:
            continue
        if now_min >= rng.start and now_min <= rng.end:
            return True
    return False

