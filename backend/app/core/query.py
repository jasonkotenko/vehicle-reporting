"""Shared query helpers for read APIs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.plates import normalize_plate
from app.core.timezone import parse_display_datetime
from app.schemas.common import PaginatedResponse


@dataclass(frozen=True)
class TimeRange:
    start: datetime | None
    end: datetime | None


def parse_time_range(from_value: str | None, to_value: str | None) -> TimeRange:
    tz_name = get_settings().display_timezone
    start = parse_display_datetime(from_value, tz_name) if from_value else None
    end = parse_display_datetime(to_value, tz_name) if to_value else None
    return TimeRange(start=start, end=end)


def apply_time_range(
    query: Select,
    column,
    time_range: TimeRange,
) -> Select:
    if time_range.start is not None:
        query = query.where(column >= time_range.start)
    if time_range.end is not None:
        query = query.where(column <= time_range.end)
    return query


def normalize_plate_query(plate: str | None) -> str | None:
    if not plate:
        return None
    return normalize_plate(plate)


def paginate(
    db: Session,
    query: Select,
    *,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)))
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


def link_vehicle(vehicle_id: UUID) -> str:
    return f"/api/v1/vehicles/{vehicle_id}"


def link_event(event_id: UUID) -> str:
    return f"/api/v1/events/{event_id}"


def link_trip(trip_id: UUID) -> str:
    return f"/api/v1/trips/{trip_id}"


def link_authorized(authorized_id: UUID) -> str:
    return f"/api/v1/admin/authorized-vehicles/{authorized_id}"
