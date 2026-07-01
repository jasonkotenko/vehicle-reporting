"""Ingest API integration tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models import VehicleEvent, VehicleProfile
from app.models.enums import AuthorizationStatus

client = TestClient(app)


@pytest.fixture
def ingest_headers() -> dict[str, str]:
    return {"X-Ingest-Key": get_settings().ingest_api_key}


def _payload(**overrides: object) -> dict:
    base = {
        "external_id": f"evt-{uuid.uuid4()}",
        "camera_id": "CAM-MAIN-ENTRY",
        "timestamp": "2026-07-01T08:15:32+08:00",
        "license_plate": "ABC1234",
        "plate_status": "READ",
        "image_urls": ["http://cv-host/snapshots/frame1.jpg"],
    }
    base.update(overrides)
    return base


def test_ingest_happy_path_creates_event(ingest_headers: dict[str, str]) -> None:
    payload = _payload(license_plate="ABC 1234")

    response = client.post("/api/v1/ingest/events", json=payload, headers=ingest_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["event_id"]
    assert body["vehicle_profile_id"]

    db = SessionLocal()
    try:
        event = db.get(VehicleEvent, body["event_id"])
        assert event is not None
        assert event.raw_plate == "ABC 1234"
        assert event.normalized_plate == "ABC1234"
        assert event.effective_plate == "ABC1234"
        assert event.authorization_status == AuthorizationStatus.AUTHORIZED
        assert event.raw_payload == payload
        assert event.image_refs == [
            {"source_url": "http://cv-host/snapshots/frame1.jpg", "status": "pending"}
        ]
        assert str(event.vehicle_profile_id) == body["vehicle_profile_id"]
    finally:
        db.close()


def test_ingest_unknown_camera_returns_422(ingest_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/ingest/events",
        json=_payload(camera_id="CAM-DOES-NOT-EXIST"),
        headers=ingest_headers,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "unknown_camera"


def test_ingest_duplicate_external_id_is_idempotent(ingest_headers: dict[str, str]) -> None:
    payload = _payload(external_id=f"dup-test-{uuid.uuid4()}")

    first = client.post("/api/v1/ingest/events", json=payload, headers=ingest_headers)
    second = client.post("/api/v1/ingest/events", json=payload, headers=ingest_headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json() == second.json()

    db = SessionLocal()
    try:
        count = db.scalar(
            select(func.count())
            .select_from(VehicleEvent)
            .where(VehicleEvent.external_id == payload["external_id"])
        )
        assert count == 1
    finally:
        db.close()


def test_ingest_unreadable_plate_with_multi_frame_urls(ingest_headers: dict[str, str]) -> None:
    payload = _payload(
        license_plate=None,
        plate_status="UNREADABLE",
        image_urls=[
            "http://cv-host/snapshots/frame1.jpg",
            "http://cv-host/snapshots/frame2.jpg",
        ],
    )

    response = client.post("/api/v1/ingest/events", json=payload, headers=ingest_headers)

    assert response.status_code == 201
    db = SessionLocal()
    try:
        event = db.get(VehicleEvent, response.json()["event_id"])
        assert event is not None
        assert event.raw_plate is None
        assert event.normalized_plate is None
        assert event.authorization_status == AuthorizationStatus.UNKNOWN
        assert len(event.image_refs) == 2
    finally:
        db.close()


def test_ingest_requires_valid_ingest_key() -> None:
    response = client.post(
        "/api/v1/ingest/events",
        json=_payload(),
        headers={"X-Ingest-Key": "wrong-key"},
    )

    assert response.status_code == 401


def test_ingest_visitor_plate(ingest_headers: dict[str, str]) -> None:
    payload = _payload(license_plate="ZZZ9999", external_id=f"visitor-{uuid.uuid4()}")

    response = client.post("/api/v1/ingest/events", json=payload, headers=ingest_headers)

    assert response.status_code == 201
    db = SessionLocal()
    try:
        event = db.get(VehicleEvent, response.json()["event_id"])
        assert event is not None
        assert event.authorization_status == AuthorizationStatus.VISITOR
    finally:
        db.close()


def test_ingest_reuses_vehicle_profile_for_same_plate(ingest_headers: dict[str, str]) -> None:
    first = client.post(
        "/api/v1/ingest/events",
        json=_payload(external_id=f"profile-a-{uuid.uuid4()}", license_plate="XYZ1111"),
        headers=ingest_headers,
    )
    second = client.post(
        "/api/v1/ingest/events",
        json=_payload(
            external_id=f"profile-b-{uuid.uuid4()}",
            license_plate="XYZ-1111",
            timestamp="2026-07-01T09:00:00+08:00",
        ),
        headers=ingest_headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["vehicle_profile_id"] == second.json()["vehicle_profile_id"]

    db = SessionLocal()
    try:
        profile_count = db.scalar(
            select(func.count())
            .select_from(VehicleProfile)
            .where(VehicleProfile.normalized_plate == "XYZ1111")
        )
        assert profile_count == 1
    finally:
        db.close()
