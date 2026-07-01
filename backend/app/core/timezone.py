"""Timezone helpers for display formatting and report filters."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def to_display(dt: datetime, tz_name: str) -> datetime:
    """Convert an aware or naive UTC datetime to the display timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ZoneInfo(tz_name))


def parse_display_datetime(value: str, tz_name: str) -> datetime:
    """
    Parse an ISO datetime string for report filters.

    Naive values are interpreted in the display timezone, then converted to UTC.
    """
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    display_tz = ZoneInfo(tz_name)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=display_tz)

    return parsed.astimezone(UTC)


def format_display_datetime(dt: datetime, tz_name: str) -> str:
    """Format a datetime for human-readable exports in the display timezone."""
    return to_display(dt, tz_name).strftime("%Y-%m-%d %H:%M:%S %Z")
