"""Plate correction and audit tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models import PlateCorrectionAudit, Trip, VehicleEvent, VehicleProfile
from app.models.enums import TripStatus

client = TestClient(app)


@pytest.fixture
def ingest_headers() -> dict[str, str]:
    return {"X-Ingest-Key": get_settings().ingest_api_key}


def _ingest_unreadable_entry(ingest_headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/ingest/events",
        headers=ingest_headers,
        json={
            "external_id": f"corr-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-ENTRY",
            "timestamp": "2026-07-05T10:00:00+08:00",
            "license_plate": None,
            "plate_status": "UNREADABLE",
            "image_urls": [
                "http://cv-host/snapshots/frame1.jpg",
                "http://cv-host/snapshots/frame2.jpg",
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["event_id"]


def test_gallery_returns_image_refs(
    operator_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    event_id = _ingest_unreadable_entry(ingest_headers)

    response = client.get(
        f"/api/v1/events/{event_id}/gallery",
        headers=operator_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["image_refs"]) == 2
    assert body["plate_status"] == "UNREADABLE"


def test_correction_moves_trip_and_creates_audit(
    operator_headers: dict[str, str],
    admin_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    event_id = _ingest_unreadable_entry(ingest_headers)
    new_plate = f"FIX{uuid.uuid4().hex[:6].upper()}"

    db = SessionLocal()
    try:
        event = db.get(VehicleEvent, event_id)
        original_payload = dict(event.raw_payload)
        old_profile_id = event.vehicle_profile_id
    finally:
        db.close()

    correct = client.post(
        f"/api/v1/events/{event_id}/correct-plate",
        headers=operator_headers,
        json={"new_plate": new_plate, "note": "readable on frame 2"},
    )
    assert correct.status_code == 200, correct.text
    body = correct.json()
    assert body["effective_plate"] == new_plate
    audit_id = body["audit_id"]

    db = SessionLocal()
    try:
        event = db.get(VehicleEvent, event_id)
        assert event is not None
        assert event.raw_payload == original_payload
        assert event.effective_plate == new_plate
        assert event.vehicle_profile_id != old_profile_id

        profile = db.scalar(select(VehicleProfile).where(VehicleProfile.normalized_plate == new_plate))
        assert profile is not None
        assert event.vehicle_profile_id == profile.id

        trip = db.scalar(select(Trip).where(Trip.vehicle_profile_id == profile.id))
        assert trip is not None
        assert trip.status == TripStatus.OPEN

        audit = db.get(PlateCorrectionAudit, audit_id)
        assert audit is not None
        assert audit.new_plate == new_plate
        assert audit.original_raw_payload == original_payload
        assert len(audit.image_refs) == 2
    finally:
        db.close()

    roster = client.get("/api/v1/roster", headers=operator_headers)
    assert any(item["plate"] == new_plate for item in roster.json())

    audit_list = client.get("/api/v1/admin/audit/corrections", headers=admin_headers)
    assert audit_list.status_code == 200
    assert any(item["id"] == audit_id for item in audit_list.json()["items"])

    audit_detail = client.get(
        f"/api/v1/admin/audit/corrections/{audit_id}",
        headers=admin_headers,
    )
    assert audit_detail.status_code == 200
    detail = audit_detail.json()
    assert detail["original_raw_payload"] == original_payload
    assert detail["corrected_by_display_name"]


def test_re_correction_creates_second_audit_entry(
    operator_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    event_id = _ingest_unreadable_entry(ingest_headers)
    first_plate = f"ONE{uuid.uuid4().hex[:5].upper()}"
    second_plate = f"TWO{uuid.uuid4().hex[:5].upper()}"

    first = client.post(
        f"/api/v1/events/{event_id}/correct-plate",
        headers=operator_headers,
        json={"new_plate": first_plate},
    )
    second = client.post(
        f"/api/v1/events/{event_id}/correct-plate",
        headers=operator_headers,
        json={"new_plate": second_plate},
    )
    assert first.status_code == 200
    assert second.status_code == 200

    db = SessionLocal()
    try:
        count = db.scalar(
            select(func.count())
            .select_from(PlateCorrectionAudit)
            .where(PlateCorrectionAudit.vehicle_event_id == event_id)
        )
        assert count == 2
    finally:
        db.close()


def test_unchanged_plate_rejected(
    operator_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    event_id = _ingest_unreadable_entry(ingest_headers)
    plate = f"SAME{uuid.uuid4().hex[:5].upper()}"

    first = client.post(
        f"/api/v1/events/{event_id}/correct-plate",
        headers=operator_headers,
        json={"new_plate": plate},
    )
    assert first.status_code == 200

    second = client.post(
        f"/api/v1/events/{event_id}/correct-plate",
        headers=operator_headers,
        json={"new_plate": plate},
    )
    assert second.status_code == 400
    assert second.json()["code"] == "unchanged_plate"


def test_audit_requires_admin(operator_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/admin/audit/corrections", headers=operator_headers)
    assert response.status_code == 403
