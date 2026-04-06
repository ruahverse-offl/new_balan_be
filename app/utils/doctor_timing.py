"""Sync doctor consultation slot boundaries: PostgreSQL TIME columns ↔ legacy display strings."""

from __future__ import annotations

import re
from datetime import datetime, time
from typing import Any, Optional, Tuple

_TIMING_KEYS = frozenset(
    {
        "morning_timings",
        "evening_timings",
        "morning_start",
        "morning_end",
        "evening_start",
        "evening_end",
    }
)


def _parse_clock_token(s: str) -> Optional[time]:
    s = (s or "").strip()
    if not s:
        return None
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)\s*$", s, re.I)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        sec = int(m.group(3) or 0)
        ap = m.group(4).upper()
        if ap == "PM" and h != 12:
            h += 12
        if ap == "AM" and h == 12:
            h = 0
        if 0 <= h <= 23 and 0 <= mi <= 59 and 0 <= sec <= 59:
            return time(h, mi, sec)
        return None
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    return None


def parse_range_times(range_str: Optional[str]) -> Tuple[Optional[time], Optional[time]]:
    if not range_str or not str(range_str).strip():
        return None, None
    parts = re.split(r"\s*-\s*", str(range_str).strip(), maxsplit=1)
    if len(parts) < 2:
        return None, None
    return _parse_clock_token(parts[0]), _parse_clock_token(parts[1])


def format_range_hhmm12(start: Optional[time], end: Optional[time]) -> Optional[str]:
    if start is None or end is None:
        return None

    def fmt12(t: time) -> str:
        h = t.hour % 12 or 12
        ap = "PM" if t.hour >= 12 else "AM"
        return f"{h}:{t.minute:02d} {ap}"

    return f"{fmt12(start)} - {fmt12(end)}"


def normalize_doctor_timing_for_orm(data: dict[str, Any], *, is_update: bool = False) -> None:
    """
    Mutates ``data`` in place before ORM create/update.

    - Fills ``morning_start`` / ``morning_end`` (and evening) from legacy strings when times are missing.
    - Fills legacy ``morning_timings`` / ``evening_timings`` from TIME when strings are missing.
    """
    if is_update and not _TIMING_KEYS.intersection(data.keys()):
        return

    if data.get("morning_timings") and (
        data.get("morning_start") is None or data.get("morning_end") is None
    ):
        p0, p1 = parse_range_times(data.get("morning_timings"))
        if data.get("morning_start") is None:
            data["morning_start"] = p0
        if data.get("morning_end") is None:
            data["morning_end"] = p1

    if data.get("evening_timings") and (
        data.get("evening_start") is None or data.get("evening_end") is None
    ):
        p0, p1 = parse_range_times(data.get("evening_timings"))
        if data.get("evening_start") is None:
            data["evening_start"] = p0
        if data.get("evening_end") is None:
            data["evening_end"] = p1

    if data.get("morning_start") is not None and data.get("morning_end") is not None:
        if not data.get("morning_timings"):
            derived = format_range_hhmm12(data["morning_start"], data["morning_end"])
            if derived:
                data["morning_timings"] = derived[:100]

    if data.get("evening_start") is not None and data.get("evening_end") is not None:
        if not data.get("evening_timings"):
            derived = format_range_hhmm12(data["evening_start"], data["evening_end"])
            if derived:
                data["evening_timings"] = derived[:100]
