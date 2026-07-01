"""Admin authorized vehicle API tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models import AuthorizedVehicle, VehicleProfile
from app.models.enums import AuthorizationStatus, VehicleCategory

client = TestClient(app)


def test_create_authorized_vehicle_normalizes_plate(admin_headers: dict[str, str]) -> None:
    plate_suffix = uuid.uuid4().hex[:6].upper()
    response = client.post(
        "/api/v1/admin/authorized-vehicles",
        headers=admin_headers,
        json={
            "plate": f"NEW {plate_suffix}",
            "category": "RESIDENT",
            "owner_name": "Maria Santos",
            "owner_address": "Block 3 Lot 9",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["normalized_plate"] == f"NEW{plate_suffix}"
    assert body["plate"] == f"NEW{plate_suffix}"
    assert body["category"] == VehicleCategory.RESIDENT.value


def test_list_and_get_authorized_vehicle(admin_headers: dict[str, str]) -> None:
    listed = client.get(
        "/api/v1/admin/authorized-vehicles",
        headers=admin_headers,
        params={"plate": "ABC", "page": 1, "page_size": 10},
    )
    assert listed.status_code == 200
    payload = listed.json()
    assert "items" in payload
    assert payload["total"] >= 1

    record_id = payload["items"][0]["id"]
    detail = client.get(
        f"/api/v1/admin/authorized-vehicles/{record_id}",
        headers=admin_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == record_id


def test_update_authorized_vehicle(admin_headers: dict[str, str]) -> None:
    plate_suffix = uuid.uuid4().hex[:6].upper()
    created = client.post(
        "/api/v1/admin/authorized-vehicles",
        headers=admin_headers,
        json={
            "plate": f"UPD {plate_suffix}",
            "category": "STAFF",
            "owner_name": "Staff Member",
            "owner_address": "Gate House",
        },
    )
    record_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/admin/authorized-vehicles/{record_id}",
        headers=admin_headers,
        json={"owner_name": "Updated Staff Member", "active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["owner_name"] == "Updated Staff Member"
    assert updated.json()["active"] is False


def test_duplicate_authorized_plate_returns_409(admin_headers: dict[str, str]) -> None:
    plate_suffix = uuid.uuid4().hex[:6].upper()
    payload = {
        "plate": f"DUP{plate_suffix}",
        "category": "SERVICE",
        "owner_name": "Service Co",
        "owner_address": "Industrial Park",
    }
    first = client.post("/api/v1/admin/authorized-vehicles", headers=admin_headers, json=payload)
    second = client.post("/api/v1/admin/authorized-vehicles", headers=admin_headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["code"] == "duplicate_plate"


def test_new_authorized_plate_tags_future_ingest(admin_headers: dict[str, str]) -> None:
    plate_suffix = uuid.uuid4().hex[:6].upper()
    normalized = f"AUTH{plate_suffix}"
    client.post(
        "/api/v1/admin/authorized-vehicles",
        headers=admin_headers,
        json={
            "plate": normalized,
            "category": "RESIDENT",
            "owner_name": "Resident",
            "owner_address": "Block 1",
        },
    )

    ingest = client.post(
        "/api/v1/ingest/events",
        headers={"X-Ingest-Key": get_settings().ingest_api_key},
        json={
            "external_id": f"auth-tag-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-ENTRY",
            "timestamp": "2026-07-01T13:00:00+08:00",
            "license_plate": normalized,
            "plate_status": "READ",
            "image_urls": ["http://cv-host/snapshots/a.jpg"],
        },
    )
    assert ingest.status_code == 201

    db = SessionLocal()
    try:
        record = db.scalar(
            select(AuthorizedVehicle).where(AuthorizedVehicle.normalized_plate == normalized)
        )
        profile = db.scalar(
            select(VehicleProfile).where(VehicleProfile.normalized_plate == normalized)
        )
        assert record is not None
        assert profile is not None
        assert profile.authorized_vehicle_id == record.id
    finally:
        db.close()

    from app.models import VehicleEvent

    db = SessionLocal()
    try:
        event = db.get(VehicleEvent, ingest.json()["event_id"])
        assert event is not None
        assert event.authorization_status == AuthorizationStatus.AUTHORIZED
    finally:
        db.close()
