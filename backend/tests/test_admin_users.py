"""Admin user management tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models import User

client = TestClient(app)


@pytest.fixture
def ingest_headers() -> dict[str, str]:
    return {"X-Ingest-Key": get_settings().ingest_api_key}


def test_list_users_requires_admin(operator_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/admin/users", headers=operator_headers)
    assert response.status_code == 403


def test_admin_user_crud(admin_headers: dict[str, str]) -> None:
    username = f"guard-{uuid.uuid4().hex[:8]}"
    create = client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "username": username,
            "password": "operator-pass",
            "display_name": "Test Guard",
            "role": "OPERATOR",
        },
    )
    assert create.status_code == 201, create.text
    user_id = create.json()["id"]
    assert create.json()["role"] == "OPERATOR"
    assert create.json()["active"] is True

    listing = client.get("/api/v1/admin/users", headers=admin_headers)
    assert listing.status_code == 200
    assert any(item["username"] == username for item in listing.json())

    update = client.patch(
        f"/api/v1/admin/users/{user_id}",
        headers=admin_headers,
        json={"display_name": "Updated Guard"},
    )
    assert update.status_code == 200
    assert update.json()["display_name"] == "Updated Guard"

    reset = client.post(
        f"/api/v1/admin/users/{user_id}/reset-password",
        headers=admin_headers,
        json={"password": "new-operator-pass"},
    )
    assert reset.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "new-operator-pass"},
    )
    assert login.status_code == 200


def test_operator_cannot_access_admin_cameras(operator_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/admin/cameras", headers=operator_headers)
    assert response.status_code == 403


def test_ingest_does_not_require_user_jwt(ingest_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/ingest/events",
        headers=ingest_headers,
        json={
            "external_id": f"auth-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-ENTRY",
            "timestamp": "2026-07-05T08:00:00+08:00",
            "license_plate": f"AUTH{uuid.uuid4().hex[:6].upper()}",
            "plate_status": "READ",
            "image_urls": ["http://cv-host/snapshots/a.jpg"],
        },
    )
    assert response.status_code == 201


def test_logout_returns_204(admin_headers: dict[str, str]) -> None:
    response = client.post("/api/v1/auth/logout", headers=admin_headers)
    assert response.status_code == 204


def test_cannot_deactivate_self(admin_headers: dict[str, str]) -> None:
    me = client.get("/api/v1/auth/me", headers=admin_headers)
    user_id = me.json()["id"]

    response = client.patch(
        f"/api/v1/admin/users/{user_id}",
        headers=admin_headers,
        json={"active": False},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "self_deactivate"


def test_create_admin_script_skips_when_users_exist() -> None:
    db = SessionLocal()
    try:
        assert db.scalar(select(User).limit(1)) is not None
    finally:
        db.close()

    from app.scripts.create_admin import create_admin

    create_admin()
