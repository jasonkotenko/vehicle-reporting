"""Image storage, fetch, and serving tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.images import validate_image_key
from app.db.session import SessionLocal
from app.main import app
from app.models import Camera, VehicleEvent, VehicleProfile
from app.models.enums import AuthorizationStatus, PlateStatus
from app.services.image_fetch import ImageFetchService
from app.services.image_storage import LocalImageStorage
from app.services.image_tokens import build_signed_image_url, create_image_access_token

client = TestClient(app)


@pytest.fixture
def image_storage_path(tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_STORAGE_PATH", str(tmp_path))
    monkeypatch.setenv("PUBLIC_API_URL", "http://testserver")
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


def _create_pending_event(db, source_url: str = "http://cv-host/snapshots/frame1.jpg") -> VehicleEvent:
    captured = datetime(2026, 7, 6, 1, 0, tzinfo=UTC)
    profile = VehicleProfile(
        normalized_plate=f"IMG{uuid.uuid4().hex[:6].upper()}",
        first_seen_at=captured,
        last_seen_at=captured,
    )
    db.add(profile)
    db.flush()
    camera = db.scalar(select(Camera).where(Camera.camera_id == "CAM-MAIN-ENTRY"))
    assert camera is not None
    event = VehicleEvent(
        camera_id=camera.id,
        vehicle_profile_id=profile.id,
        captured_at=captured,
        raw_plate=profile.normalized_plate,
        normalized_plate=profile.normalized_plate,
        effective_plate=profile.normalized_plate,
        plate_status=PlateStatus.READ,
        image_refs=[{"source_url": source_url, "status": "pending"}],
        raw_payload={"test": True},
        authorization_status=AuthorizationStatus.VISITOR,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def test_local_storage_roundtrip(image_storage_path) -> None:
    storage = LocalImageStorage(str(image_storage_path))
    key = storage.store(b"fake-image", "image/jpeg")
    validate_image_key(key)
    content, content_type = storage.read(key)
    assert content == b"fake-image"
    assert content_type == "image/jpeg"


def test_validate_image_key_rejects_traversal() -> None:
    with pytest.raises(ValueError):
        validate_image_key("../etc/passwd")
    with pytest.raises(ValueError):
        validate_image_key("ab/../../secret.jpg")


def test_fetch_stores_image_and_updates_refs(image_storage_path) -> None:
    db = SessionLocal()
    try:
        event = _create_pending_event(db)
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_bytes = MagicMock(return_value=iter([b"jpeg-data"]))

        with patch("app.services.image_fetch.httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = False
            mock_client.stream.return_value.__enter__.return_value = mock_response
            mock_client.stream.return_value.__exit__.return_value = False

            ImageFetchService().fetch_event_images(event.id)

        db.refresh(event)
        assert event.image_refs[0]["status"] == "stored"
        assert event.image_refs[0]["key"]
        storage = LocalImageStorage(str(image_storage_path))
        assert storage.exists(event.image_refs[0]["key"])
    finally:
        db.close()


def test_fetch_failure_marks_ref(image_storage_path) -> None:
    db = SessionLocal()
    try:
        event = _create_pending_event(db)

        with patch("app.services.image_fetch.httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = False
            mock_client.stream.side_effect = httpx.HTTPError("network down")

            ImageFetchService().fetch_event_images(event.id)

        db.refresh(event)
        assert event.image_refs[0]["status"] == "fetch_failed"
        assert event.image_refs[0]["error"]
    finally:
        db.close()


def test_allowlist_blocks_disallowed_url(image_storage_path, monkeypatch) -> None:
    monkeypatch.setenv("CV_IMAGE_URL_ALLOWLIST", "http://allowed.example")
    get_settings.cache_clear()

    db = SessionLocal()
    try:
        event = _create_pending_event(db, source_url="http://cv-host/snapshots/frame1.jpg")
        ImageFetchService().fetch_event_images(event.id)
        db.refresh(event)
        assert event.image_refs[0]["status"] == "fetch_failed"
        assert event.image_refs[0]["error"] == "url_not_allowed"
    finally:
        db.close()
        monkeypatch.delenv("CV_IMAGE_URL_ALLOWLIST", raising=False)
        get_settings.cache_clear()


def test_serve_image_requires_token(image_storage_path) -> None:
    storage = LocalImageStorage(str(image_storage_path))
    key = storage.store(b"img-bytes", "image/jpeg")

    response = client.get(f"/api/v1/images/{key}")
    assert response.status_code == 422

    response = client.get(f"/api/v1/images/{key}", params={"token": "invalid"})
    assert response.status_code == 403


def test_serve_image_with_valid_token(image_storage_path) -> None:
    storage = LocalImageStorage(str(image_storage_path))
    key = storage.store(b"img-bytes", "image/jpeg")
    token = create_image_access_token(key)

    response = client.get(f"/api/v1/images/{key}", params={"token": token})
    assert response.status_code == 200
    assert response.content == b"img-bytes"
    assert response.headers["content-type"].startswith("image/jpeg")


def test_unknown_image_key_returns_404(image_storage_path) -> None:
    key = "ab/notfound1234567890abcdef1234567890ab.jpg"
    token = create_image_access_token(key)
    response = client.get(f"/api/v1/images/{key}", params={"token": token})
    assert response.status_code == 404


def test_gallery_includes_signed_url_after_fetch(
    image_storage_path,
    operator_headers: dict[str, str],
) -> None:
    db = SessionLocal()
    try:
        event = _create_pending_event(db)
        storage = LocalImageStorage(str(image_storage_path))
        key = storage.store(b"gallery", "image/jpeg")
        event.image_refs = [
            {
                "source_url": "http://cv-host/snapshots/frame1.jpg",
                "status": "stored",
                "key": key,
                "content_type": "image/jpeg",
            }
        ]
        db.commit()
        event_id = str(event.id)
    finally:
        db.close()

    response = client.get(f"/api/v1/events/{event_id}/gallery", headers=operator_headers)
    assert response.status_code == 200
    ref = response.json()["image_refs"][0]
    assert ref["signed_url"] == build_signed_image_url(key)


def test_event_image_redirect_requires_operator_auth(image_storage_path) -> None:
    db = SessionLocal()
    try:
        event = _create_pending_event(db)
        storage = LocalImageStorage(str(image_storage_path))
        key = storage.store(b"redirect", "image/jpeg")
        event.image_refs = [
            {
                "source_url": "http://cv-host/snapshots/frame1.jpg",
                "status": "stored",
                "key": key,
            }
        ]
        db.commit()
        event_id = event.id
    finally:
        db.close()

    response = client.get(f"/api/v1/events/{event_id}/images/0", follow_redirects=False)
    assert response.status_code == 401
