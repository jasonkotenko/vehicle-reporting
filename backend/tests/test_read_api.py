"""Read and reporting API integration tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models import Trip, VehicleProfile
from app.models.enums import TripStatus

client = TestClient(app)


@pytest.fixture
def ingest_headers() -> dict[str, str]:
    return {"X-Ingest-Key": get_settings().ingest_api_key}


def _ingest_sequence(ingest_headers: dict[str, str], plate: str) -> dict:
    base = {
        "license_plate": plate,
        "plate_status": "READ",
        "image_urls": ["http://cv-host/snapshots/a.jpg"],
    }
    entry = client.post(
        "/api/v1/ingest/events",
        headers=ingest_headers,
        json={
            **base,
            "external_id": f"read-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-ENTRY",
            "timestamp": "2026-07-03T09:00:00+08:00",
        },
    )
    internal = client.post(
        "/api/v1/ingest/events",
        headers=ingest_headers,
        json={
            **base,
            "external_id": f"read-{uuid.uuid4()}",
            "camera_id": "CAM-INT-01",
            "timestamp": "2026-07-03T09:05:00+08:00",
        },
    )
    exit_evt = client.post(
        "/api/v1/ingest/events",
        headers=ingest_headers,
        json={
            **base,
            "external_id": f"read-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-EXIT",
            "timestamp": "2026-07-03T09:10:00+08:00",
        },
    )
    assert entry.status_code == 201
    assert internal.status_code == 201
    assert exit_evt.status_code == 201
    return {
        "entry_event_id": entry.json()["event_id"],
        "exit_event_id": exit_evt.json()["event_id"],
        "vehicle_profile_id": entry.json()["vehicle_profile_id"],
    }


def test_read_endpoints_require_auth() -> None:
    response = client.get("/api/v1/vehicles")
    assert response.status_code == 401


def test_vehicle_search_and_detail(
    operator_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"READ{uuid.uuid4().hex[:6].upper()}"
    created = _ingest_sequence(ingest_headers, plate)

    search = client.get(
        "/api/v1/vehicles",
        headers=operator_headers,
        params={"plate": plate[:6]},
    )
    assert search.status_code == 200
    body = search.json()
    assert body["total"] >= 1
    assert any(item["normalized_plate"] == plate for item in body["items"])

    detail = client.get(
        f"/api/v1/vehicles/{created['vehicle_profile_id']}",
        headers=operator_headers,
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["plate"] == plate
    assert detail_body["event_count"] == 3
    assert detail_body["trip_count"] == 1
    assert detail_body["links"]["self"].endswith(created["vehicle_profile_id"])


def test_vehicle_events_and_trips(
    operator_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"EVT{uuid.uuid4().hex[:6].upper()}"
    created = _ingest_sequence(ingest_headers, plate)

    events = client.get(
        f"/api/v1/vehicles/{created['vehicle_profile_id']}/events",
        headers=operator_headers,
    )
    assert events.status_code == 200
    assert events.json()["total"] == 3
    assert events.json()["items"][0]["camera_id"] in {
        "CAM-MAIN-ENTRY",
        "CAM-INT-01",
        "CAM-MAIN-EXIT",
    }

    trips = client.get(
        f"/api/v1/vehicles/{created['vehicle_profile_id']}/trips",
        headers=operator_headers,
    )
    assert trips.status_code == 200
    assert trips.json()["total"] == 1
    assert trips.json()["items"][0]["status"] == "COMPLETE"
    assert trips.json()["items"][0]["event_count"] == 3


def test_event_list_and_detail_with_trip_link(
    operator_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"DET{uuid.uuid4().hex[:6].upper()}"
    created = _ingest_sequence(ingest_headers, plate)

    listing = client.get(
        "/api/v1/events",
        headers=operator_headers,
        params={"plate": plate},
    )
    assert listing.status_code == 200
    assert listing.json()["total"] == 3

    detail = client.get(
        f"/api/v1/events/{created['entry_event_id']}",
        headers=operator_headers,
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["vehicle_profile_id"] == created["vehicle_profile_id"]
    assert detail_body["trip_id"]
    assert detail_body["links"]["trip"]
    assert detail_body["raw_payload"]["license_plate"] == plate


def test_trip_detail_includes_ordered_events(
    operator_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"TRP{uuid.uuid4().hex[:6].upper()}"
    created = _ingest_sequence(ingest_headers, plate)

    db = SessionLocal()
    try:
        profile = db.scalar(select(VehicleProfile).where(VehicleProfile.normalized_plate == plate))
        trip = db.scalar(select(Trip).where(Trip.vehicle_profile_id == profile.id))
        trip_id = str(trip.id)
    finally:
        db.close()

    response = client.get(f"/api/v1/trips/{trip_id}", headers=operator_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETE"
    assert len(body["events"]) == 3
    assert body["events"][0]["zone_type"] == "ENTRY"
    assert body["events"][1]["zone_type"] == "INTERNAL"
    assert body["events"][2]["zone_type"] == "EXIT"
    assert body["events"][0]["links"]["trip"] == f"/api/v1/trips/{trip_id}"


def test_roster_shows_open_trips(
    operator_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"ROS{uuid.uuid4().hex[:6].upper()}"
    client.post(
        "/api/v1/ingest/events",
        headers=ingest_headers,
        json={
            "external_id": f"read-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-ENTRY",
            "timestamp": "2026-07-03T10:00:00+08:00",
            "license_plate": plate,
            "plate_status": "READ",
            "image_urls": ["http://cv-host/snapshots/a.jpg"],
        },
    )

    roster = client.get("/api/v1/roster", headers=operator_headers)
    assert roster.status_code == 200
    assert any(item["plate"] == plate for item in roster.json())


def test_reports_entries_exits_and_trips(
    admin_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"RPT{uuid.uuid4().hex[:6].upper()}"
    _ingest_sequence(ingest_headers, plate)

    params = {
        "from": "2026-07-03T00:00:00+08:00",
        "to": "2026-07-03T23:59:59+08:00",
        "plate": plate,
    }

    entries = client.get("/api/v1/reports/entries", headers=admin_headers, params=params)
    exits = client.get("/api/v1/reports/exits", headers=admin_headers, params=params)
    trips = client.get(
        "/api/v1/reports/trips",
        headers=admin_headers,
        params={**params, "status": "COMPLETE"},
    )

    assert entries.status_code == 200
    assert exits.status_code == 200
    assert trips.status_code == 200
    assert entries.json()["total"] == 1
    assert exits.json()["total"] == 1
    assert trips.json()["total"] == 1


def test_reports_transits_filter_by_camera(
    admin_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"TRN{uuid.uuid4().hex[:6].upper()}"
    _ingest_sequence(ingest_headers, plate)

    response = client.get(
        "/api/v1/reports/transits",
        headers=admin_headers,
        params={
            "camera_ids": ["CAM-INT-01"],
            "from": "2026-07-03T00:00:00+08:00",
            "to": "2026-07-03T23:59:59+08:00",
            "plate": plate,
        },
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["camera_label"]


def test_incomplete_trips_in_report(
    admin_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"INC{uuid.uuid4().hex[:6].upper()}"
    client.post(
        "/api/v1/ingest/events",
        headers=ingest_headers,
        json={
            "external_id": f"read-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-EXIT",
            "timestamp": "2026-07-03T11:00:00+08:00",
            "license_plate": plate,
            "plate_status": "READ",
            "image_urls": ["http://cv-host/snapshots/a.jpg"],
        },
    )

    response = client.get(
        "/api/v1/reports/trips",
        headers=admin_headers,
        params={
            "status": "INCOMPLETE",
            "plate": plate,
            "from": "2026-07-03T00:00:00+08:00",
            "to": "2026-07-03T23:59:59+08:00",
        },
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["status"] == "INCOMPLETE"


def test_reports_require_admin(operator_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/reports/entries", headers=operator_headers)
    assert response.status_code == 403
