"""Report export filters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.core.query import TimeRange
from app.models.enums import TripStatus


class ReportType(StrEnum):
    ENTRIES = "entries"
    EXITS = "exits"
    TRANSITS = "transits"
    TRIPS = "trips"
    ROSTER = "roster"


@dataclass(frozen=True)
class ExportFilters:
    time_range: TimeRange
    plate: str | None = None
    camera_ids: list[str] | None = None
    status: TripStatus | None = None
    from_raw: str | None = None
    to_raw: str | None = None
