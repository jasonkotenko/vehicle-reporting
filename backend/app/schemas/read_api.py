"""Pydantic schemas for read/query APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import AuthorizationStatus, PlateStatus, TripStatus, ZoneType


class EntityLinks(BaseModel):
    self: str
    vehicle: str | None = None
    trip: str | None = None
    event: str | None = None
    authorized: str | None = None


class VehicleProfileBrief(BaseModel):
    id: UUID
    plate: str | None


class VehicleProfileDetail(BaseModel):
    id: UUID
    plate: str | None
    normalized_plate: str | None
    first_seen_at: datetime
    last_seen_at: datetime
    event_count: int
    trip_count: int
    authorized_vehicle_id: UUID | None = None
    links: EntityLinks


class TripSummary(BaseModel):
    id: UUID
    status: TripStatus
    started_at: datetime | None
    ended_at: datetime | None
    vehicle_profile: VehicleProfileBrief
    authorization_status: AuthorizationStatus | None = None
    event_count: int
    links: EntityLinks


class TripEventView(BaseModel):
    id: UUID
    sequence: int
    captured_at: datetime
    plate: str | None
    plate_status: PlateStatus
    zone_type: ZoneType
    camera_id: str
    camera_label: str
    image_refs: list
    links: EntityLinks


class TripDetailResponse(BaseModel):
    id: UUID
    status: TripStatus
    started_at: datetime | None
    ended_at: datetime | None
    vehicle_profile: VehicleProfileBrief
    authorization_status: AuthorizationStatus | None = None
    events: list[TripEventView]
    links: EntityLinks


class EventSummary(BaseModel):
    id: UUID
    captured_at: datetime
    plate: str | None
    effective_plate: str | None
    plate_status: PlateStatus
    authorization_status: AuthorizationStatus
    camera_id: str
    camera_label: str
    zone_type: ZoneType
    links: EntityLinks


class EventDetailResponse(EventSummary):
    vehicle_profile_id: UUID
    trip_id: UUID | None = None
    image_refs: list
    raw_payload: dict
    links: EntityLinks


class RosterItem(BaseModel):
    vehicle_profile_id: UUID
    plate: str | None
    entry_time: datetime
    authorization_status: AuthorizationStatus
    trip_id: UUID
    links: EntityLinks


class ReportEventRow(BaseModel):
    plate: str | None
    event_time: datetime
    camera_label: str
    authorization_status: AuthorizationStatus
    trip_id: UUID | None = None
    trip_status: TripStatus | None = None
    links: EntityLinks


class VehicleSearchItem(BaseModel):
    id: UUID
    plate: str | None
    normalized_plate: str | None
    last_seen_at: datetime
    links: EntityLinks
