"""Unit tests for ingest service logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import Camera, VehicleEvent
from app.models.enums import ZoneType
from app.schemas.ingest import IngestEventRequest
from app.services.ingest import IngestService
from app.services.ingest_errors import IngestError


def test_process_event_rejects_unknown_camera() -> None:
    db = SessionLocal()
    service = IngestService()
    payload = IngestEventRequest.model_validate(
        {
            "camera_id": "CAM-MISSING",
            "timestamp": "2026-07-01T08:15:32+08:00",
            "license_plate": "AAA1111",
            "plate_status": "READ",
            "image_urls": ["http://cv-host/snapshots/a.jpg"],
        }
    )
    raw_payload = payload.model_dump(mode="json")

    try:
        with pytest.raises(IngestError) as exc_info:
            service.process_event(db, payload, raw_payload=raw_payload)
        assert exc_info.value.code == "unknown_camera"
        db.rollback()
    finally:
        db.close()


def test_process_event_fallback_dedupe_without_external_id() -> None:
    db = SessionLocal()
    service = IngestService()
    camera = Camera(
        camera_id=f"CAM-TEST-{uuid.uuid4().hex[:8]}",
        label="Test Camera",
        zone_type=ZoneType.ENTRY,
    )
    db.add(camera)
    db.commit()

    plate_suffix = uuid.uuid4().hex[:6].upper()
    normalized_plate = f"DEDUP{plate_suffix}"
    captured_at = datetime(2026, 7, 1, 8, 15, 32, tzinfo=UTC)
    raw_payload = {
        "camera_id": camera.camera_id,
        "timestamp": captured_at.isoformat().replace("+00:00", "Z"),
        "license_plate": normalized_plate,
        "plate_status": "READ",
        "image_urls": ["http://cv-host/snapshots/a.jpg"],
    }
    payload = IngestEventRequest.model_validate(raw_payload)

    try:
        first = service.process_event(db, payload, raw_payload=raw_payload)
        second = service.process_event(db, payload, raw_payload=raw_payload)

        assert first.is_duplicate is False
        assert second.is_duplicate is True
        assert first.event_id == second.event_id

        event_count = db.scalar(
            select(func.count())
            .select_from(VehicleEvent)
            .where(VehicleEvent.normalized_plate == normalized_plate)
        )
        assert event_count == 1
    finally:
        db.rollback()
        db.close()
