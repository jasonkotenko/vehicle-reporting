"""Trip computation from vehicle events and camera zones."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Camera, Trip, TripEvent, VehicleEvent, VehicleProfile
from app.models.enums import AuthorizationStatus, TripStatus, ZoneType


@dataclass(frozen=True)
class RosterEntry:
    vehicle_profile_id: UUID
    normalized_plate: str | None
    entry_time: datetime
    authorization_status: AuthorizationStatus
    trip_id: UUID


@dataclass(frozen=True)
class TripEventDetail:
    event: VehicleEvent
    camera: Camera
    sequence: int


@dataclass(frozen=True)
class TripDetail:
    trip: Trip
    events: list[TripEventDetail]


@dataclass
class _TripAccumulator:
    vehicle_profile_id: UUID
    status: TripStatus
    events: list[VehicleEvent] = field(default_factory=list)
    zones: list[ZoneType] = field(default_factory=list)

    def add_event(self, event: VehicleEvent, zone_type: ZoneType) -> None:
        self.events.append(event)
        self.zones.append(zone_type)

    def persist(self, db: Session) -> Trip:
        if not self.events:
            raise ValueError("Cannot persist trip without events")

        first_event = self.events[0]
        last_event = self.events[-1]
        first_zone = self.zones[0]
        last_zone = self.zones[-1]

        trip = Trip(
            vehicle_profile_id=self.vehicle_profile_id,
            status=self.status,
        )

        if self.status == TripStatus.OPEN:
            trip.started_at = first_event.captured_at
            trip.entry_event_id = first_event.id
        elif self.status == TripStatus.COMPLETE:
            trip.started_at = first_event.captured_at
            trip.ended_at = last_event.captured_at
            trip.entry_event_id = first_event.id
            trip.exit_event_id = last_event.id
        elif last_zone == ZoneType.EXIT and first_zone != ZoneType.ENTRY:
            trip.ended_at = last_event.captured_at
            trip.exit_event_id = last_event.id
        elif first_zone == ZoneType.ENTRY:
            trip.started_at = first_event.captured_at
            trip.entry_event_id = first_event.id
        else:
            trip.started_at = first_event.captured_at

        db.add(trip)
        db.flush()

        for sequence, event in enumerate(self.events):
            db.add(
                TripEvent(
                    trip_id=trip.id,
                    vehicle_event_id=event.id,
                    sequence=sequence,
                )
            )
        return trip


def recompute_trips_for_profile(db: Session, vehicle_profile_id: UUID) -> None:
    """Rebuild all trips for a vehicle profile from its events."""
    db.execute(delete(Trip).where(Trip.vehicle_profile_id == vehicle_profile_id))

    rows = db.execute(
        select(VehicleEvent, Camera)
        .join(Camera, VehicleEvent.camera_id == Camera.id)
        .where(VehicleEvent.vehicle_profile_id == vehicle_profile_id)
        .order_by(VehicleEvent.captured_at.asc(), VehicleEvent.id.asc())
    ).all()

    open_trip: _TripAccumulator | None = None
    orphan_internal_trip: _TripAccumulator | None = None

    for event, camera in rows:
        zone_type = camera.zone_type

        if zone_type == ZoneType.ENTRY:
            if open_trip is not None:
                open_trip.status = TripStatus.INCOMPLETE
                open_trip.persist(db)
                open_trip = None

            open_trip = _TripAccumulator(
                vehicle_profile_id=vehicle_profile_id,
                status=TripStatus.OPEN,
            )
            open_trip.add_event(event, zone_type)

        elif zone_type == ZoneType.INTERNAL:
            if open_trip is not None:
                open_trip.add_event(event, zone_type)
            elif orphan_internal_trip is not None:
                orphan_internal_trip.add_event(event, zone_type)
            else:
                orphan_internal_trip = _TripAccumulator(
                    vehicle_profile_id=vehicle_profile_id,
                    status=TripStatus.INCOMPLETE,
                )
                orphan_internal_trip.add_event(event, zone_type)

        elif zone_type == ZoneType.EXIT:
            if open_trip is not None:
                open_trip.add_event(event, zone_type)
                open_trip.status = TripStatus.COMPLETE
                open_trip.persist(db)
                open_trip = None
            else:
                exit_only = _TripAccumulator(
                    vehicle_profile_id=vehicle_profile_id,
                    status=TripStatus.INCOMPLETE,
                )
                exit_only.add_event(event, zone_type)
                exit_only.persist(db)

    if open_trip is not None:
        open_trip.persist(db)

    if orphan_internal_trip is not None:
        orphan_internal_trip.persist(db)

    db.flush()


def get_active_roster(db: Session) -> list[RosterEntry]:
    """Return vehicle profiles with an open trip (currently inside the village)."""
    rows = db.execute(
        select(Trip, VehicleProfile, VehicleEvent)
        .join(VehicleProfile, Trip.vehicle_profile_id == VehicleProfile.id)
        .join(VehicleEvent, Trip.entry_event_id == VehicleEvent.id)
        .where(Trip.status == TripStatus.OPEN)
        .order_by(Trip.started_at.desc())
    ).all()

    return [
        RosterEntry(
            vehicle_profile_id=profile.id,
            normalized_plate=profile.normalized_plate,
            entry_time=trip.started_at or event.captured_at,
            authorization_status=event.authorization_status,
            trip_id=trip.id,
        )
        for trip, profile, event in rows
    ]


def get_trip_with_events(db: Session, trip_id: UUID) -> TripDetail:
    """Load a trip and its ordered events."""
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise ValueError(f"Trip not found: {trip_id}")

    rows = db.execute(
        select(VehicleEvent, Camera, TripEvent.sequence)
        .join(TripEvent, TripEvent.vehicle_event_id == VehicleEvent.id)
        .join(Camera, VehicleEvent.camera_id == Camera.id)
        .where(TripEvent.trip_id == trip_id)
        .order_by(TripEvent.sequence.asc())
    ).all()

    events = [
        TripEventDetail(event=event, camera=camera, sequence=sequence)
        for event, camera, sequence in rows
    ]
    return TripDetail(trip=trip, events=events)
