"""Trip computation service tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models import Camera, Trip, VehicleEvent, VehicleProfile
from app.models.enums import AuthorizationStatus, PlateStatus, TripStatus, ZoneType
from app.services.trips import get_active_roster, get_trip_with_events, recompute_trips_for_profile

client = TestClient(app)


def _ts(minutes: int) -> datetime:
    return datetime(2026, 7, 1, 8, 0, tzinfo=UTC) + timedelta(minutes=minutes)


@pytest.fixture
def trip_db():
    db = SessionLocal()
    try:
        profile = VehicleProfile(
            normalized_plate=f"TRIP{uuid.uuid4().hex[:6].upper()}",
            first_seen_at=_ts(0),
            last_seen_at=_ts(0),
        )
        db.add(profile)
        db.flush()

        entry_camera = db.scalar(select(Camera).where(Camera.camera_id == "CAM-MAIN-ENTRY"))
        exit_camera = db.scalar(select(Camera).where(Camera.camera_id == "CAM-MAIN-EXIT"))
        internal_camera = db.scalar(select(Camera).where(Camera.camera_id == "CAM-INT-01"))
        assert entry_camera and exit_camera and internal_camera

        yield {
            "db": db,
            "profile": profile,
            "entry_camera": entry_camera,
            "exit_camera": exit_camera,
            "internal_camera": internal_camera,
        }
        db.rollback()
    finally:
        db.close()


def _add_event(
    db,
    profile: VehicleProfile,
    camera: Camera,
    captured_at: datetime,
) -> VehicleEvent:
    event = VehicleEvent(
        camera_id=camera.id,
        vehicle_profile_id=profile.id,
        captured_at=captured_at,
        raw_plate=profile.normalized_plate,
        normalized_plate=profile.normalized_plate,
        effective_plate=profile.normalized_plate,
        plate_status=PlateStatus.READ,
        image_refs=[],
        raw_payload={"test": True},
        authorization_status=AuthorizationStatus.VISITOR,
    )
    db.add(event)
    db.flush()
    return event


def test_standard_entry_internal_exit_trip(trip_db: dict) -> None:
    db = trip_db["db"]
    profile = trip_db["profile"]

    _add_event(db, profile, trip_db["entry_camera"], _ts(0))
    _add_event(db, profile, trip_db["internal_camera"], _ts(5))
    _add_event(db, profile, trip_db["exit_camera"], _ts(10))

    recompute_trips_for_profile(db, profile.id)
    db.commit()

    trips = list(db.scalars(select(Trip).where(Trip.vehicle_profile_id == profile.id)))
    assert len(trips) == 1
    assert trips[0].status == TripStatus.COMPLETE

    detail = get_trip_with_events(db, trips[0].id)
    assert len(detail.events) == 3
    assert detail.events[0].camera.zone_type == ZoneType.ENTRY
    assert detail.events[1].camera.zone_type == ZoneType.INTERNAL
    assert detail.events[2].camera.zone_type == ZoneType.EXIT


def test_entry_only_creates_open_trip(trip_db: dict) -> None:
    db = trip_db["db"]
    profile = trip_db["profile"]

    _add_event(db, profile, trip_db["entry_camera"], _ts(0))
    recompute_trips_for_profile(db, profile.id)
    db.commit()

    trip = db.scalar(select(Trip).where(Trip.vehicle_profile_id == profile.id))
    assert trip is not None
    assert trip.status == TripStatus.OPEN

    roster = get_active_roster(db)
    assert any(entry.trip_id == trip.id for entry in roster)


def test_exit_only_creates_incomplete_trip(trip_db: dict) -> None:
    db = trip_db["db"]
    profile = trip_db["profile"]

    _add_event(db, profile, trip_db["exit_camera"], _ts(0))
    recompute_trips_for_profile(db, profile.id)
    db.commit()

    trip = db.scalar(select(Trip).where(Trip.vehicle_profile_id == profile.id))
    assert trip is not None
    assert trip.status == TripStatus.INCOMPLETE
    assert trip.entry_event_id is None
    assert trip.exit_event_id is not None


def test_double_entry_marks_first_incomplete(trip_db: dict) -> None:
    db = trip_db["db"]
    profile = trip_db["profile"]

    _add_event(db, profile, trip_db["entry_camera"], _ts(0))
    _add_event(db, profile, trip_db["entry_camera"], _ts(5))
    recompute_trips_for_profile(db, profile.id)
    db.commit()

    trips = list(
        db.scalars(
            select(Trip)
            .where(Trip.vehicle_profile_id == profile.id)
            .order_by(Trip.started_at.asc())
        )
    )
    assert len(trips) == 2
    assert trips[0].status == TripStatus.INCOMPLETE
    assert trips[1].status == TripStatus.OPEN


def test_internal_without_entry_creates_incomplete_trip(trip_db: dict) -> None:
    db = trip_db["db"]
    profile = trip_db["profile"]

    _add_event(db, profile, trip_db["internal_camera"], _ts(0))
    _add_event(db, profile, trip_db["internal_camera"], _ts(2))
    recompute_trips_for_profile(db, profile.id)
    db.commit()

    trip = db.scalar(select(Trip).where(Trip.vehicle_profile_id == profile.id))
    assert trip is not None
    assert trip.status == TripStatus.INCOMPLETE
    assert trip.entry_event_id is None

    detail = get_trip_with_events(db, trip.id)
    assert len(detail.events) == 2


def test_ingest_sequence_builds_complete_trip() -> None:
    plate = f"INGEST{uuid.uuid4().hex[:6].upper()}"
    headers = {"X-Ingest-Key": get_settings().ingest_api_key}
    base = {
        "license_plate": plate,
        "plate_status": "READ",
        "image_urls": ["http://cv-host/snapshots/a.jpg"],
    }

    first = client.post(
        "/api/v1/ingest/events",
        headers=headers,
        json={
            **base,
            "external_id": f"trip-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-ENTRY",
            "timestamp": "2026-07-02T08:00:00+08:00",
        },
    )
    second = client.post(
        "/api/v1/ingest/events",
        headers=headers,
        json={
            **base,
            "external_id": f"trip-{uuid.uuid4()}",
            "camera_id": "CAM-INT-01",
            "timestamp": "2026-07-02T08:10:00+08:00",
        },
    )
    third = client.post(
        "/api/v1/ingest/events",
        headers=headers,
        json={
            **base,
            "external_id": f"trip-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-EXIT",
            "timestamp": "2026-07-02T08:20:00+08:00",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 201

    db = SessionLocal()
    try:
        profile = db.scalar(select(VehicleProfile).where(VehicleProfile.normalized_plate == plate))
        assert profile is not None

        trip = db.scalar(select(Trip).where(Trip.vehicle_profile_id == profile.id))
        assert trip is not None
        assert trip.status == TripStatus.COMPLETE

        detail = get_trip_with_events(db, trip.id)
        assert len(detail.events) == 3
        assert all(event.event.image_refs for event in detail.events)
    finally:
        db.close()
