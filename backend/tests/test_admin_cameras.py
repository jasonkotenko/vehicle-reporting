"""Admin camera API tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_cameras_requires_admin(operator_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/admin/cameras", headers=operator_headers)
    assert response.status_code == 403


def test_create_list_get_update_deactivate_camera(admin_headers: dict[str, str]) -> None:
    camera_code = f"CAM-TEST-{uuid.uuid4().hex[:8]}"
    create = client.post(
        "/api/v1/admin/cameras",
        headers=admin_headers,
        json={
            "camera_id": camera_code,
            "label": "Test Entry",
            "zone_type": "ENTRY",
        },
    )
    assert create.status_code == 201, create.text
    created = create.json()
    assert created["camera_id"] == camera_code
    assert created["active"] is True

    listed = client.get("/api/v1/admin/cameras", headers=admin_headers)
    assert listed.status_code == 200
    assert any(item["camera_id"] == camera_code for item in listed.json())

    detail = client.get(f"/api/v1/admin/cameras/{created['id']}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["label"] == "Test Entry"

    updated = client.patch(
        f"/api/v1/admin/cameras/{created['id']}",
        headers=admin_headers,
        json={"label": "Updated Label", "zone_type": "INTERNAL"},
    )
    assert updated.status_code == 200
    assert updated.json()["label"] == "Updated Label"
    assert updated.json()["zone_type"] == "INTERNAL"

    deactivated = client.delete(f"/api/v1/admin/cameras/{created['id']}", headers=admin_headers)
    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False


def test_create_duplicate_camera_returns_409(admin_headers: dict[str, str]) -> None:
    camera_code = f"CAM-DUP-{uuid.uuid4().hex[:8]}"
    payload = {
        "camera_id": camera_code,
        "label": "Duplicate Test",
        "zone_type": "EXIT",
    }
    first = client.post("/api/v1/admin/cameras", headers=admin_headers, json=payload)
    second = client.post("/api/v1/admin/cameras", headers=admin_headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["code"] == "duplicate_camera_id"


def test_deactivated_camera_rejects_ingest(admin_headers: dict[str, str]) -> None:
    from app.core.config import get_settings

    camera_code = f"CAM-OFF-{uuid.uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/admin/cameras",
        headers=admin_headers,
        json={
            "camera_id": camera_code,
            "label": "Offline Camera",
            "zone_type": "ENTRY",
        },
    )
    camera_id = created.json()["id"]
    client.delete(f"/api/v1/admin/cameras/{camera_id}", headers=admin_headers)

    ingest = client.post(
        "/api/v1/ingest/events",
        headers={"X-Ingest-Key": get_settings().ingest_api_key},
        json={
            "external_id": f"inactive-cam-{uuid.uuid4()}",
            "camera_id": camera_code,
            "timestamp": "2026-07-01T12:00:00+08:00",
            "license_plate": "AAA0001",
            "plate_status": "READ",
            "image_urls": ["http://cv-host/snapshots/a.jpg"],
        },
    )
    assert ingest.status_code == 422
    assert ingest.json()["code"] == "unknown_camera"
