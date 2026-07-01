"""CV/ALPR event ingest business logic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.plates import normalize_plate
from app.models import AuthorizedVehicle, Camera, VehicleEvent, VehicleProfile
from app.models.enums import AuthorizationStatus
from app.schemas.ingest import IngestEventRequest
from app.services.ingest_errors import IngestError
from app.services.trips import recompute_trips_for_profile


@dataclass(frozen=True)
class IngestResult:
    event_id: UUID
    vehicle_profile_id: UUID
    is_duplicate: bool = False


class IngestService:
    def process_event(
        self,
        db: Session,
        payload: IngestEventRequest,
        *,
        raw_payload: dict,
    ) -> IngestResult:
        captured_at = _to_utc(payload.timestamp)
        normalized_plate = normalize_plate(payload.license_plate)

        if payload.external_id:
            duplicate = self._find_by_external_id(db, payload.external_id)
            if duplicate is not None:
                if not _payloads_match(duplicate.raw_payload, raw_payload):
                    raise IngestError(
                        "Duplicate external_id with conflicting payload",
                        code="conflicting_duplicate",
                        status_code=409,
                    )
                return IngestResult(
                    event_id=duplicate.id,
                    vehicle_profile_id=duplicate.vehicle_profile_id,
                    is_duplicate=True,
                )

        camera = db.scalar(
            select(Camera).where(
                Camera.camera_id == payload.camera_id,
                Camera.active.is_(True),
            )
        )
        if camera is None:
            raise IngestError(
                f"Unknown or inactive camera: {payload.camera_id}",
                code="unknown_camera",
            )

        if payload.external_id is None:
            duplicate = self._find_by_capture_key(
                db,
                camera_id=camera.id,
                captured_at=captured_at,
                normalized_plate=normalized_plate,
            )
            if duplicate is not None:
                return IngestResult(
                    event_id=duplicate.id,
                    vehicle_profile_id=duplicate.vehicle_profile_id,
                    is_duplicate=True,
                )

        authorization_status = self._resolve_authorization(db, normalized_plate)
        profile = self._upsert_vehicle_profile(
            db,
            normalized_plate=normalized_plate,
            captured_at=captured_at,
        )

        event = VehicleEvent(
            external_id=payload.external_id,
            camera_id=camera.id,
            vehicle_profile_id=profile.id,
            captured_at=captured_at,
            raw_plate=payload.license_plate,
            normalized_plate=normalized_plate,
            effective_plate=normalized_plate,
            plate_status=payload.plate_status,
            image_refs=_pending_image_refs(payload.image_urls),
            raw_payload=raw_payload,
            authorization_status=authorization_status,
        )
        db.add(event)
        db.flush()

        recompute_trips_for_profile(db, profile.id)
        db.commit()
        db.refresh(event)

        return IngestResult(
            event_id=event.id,
            vehicle_profile_id=profile.id,
        )

    def _find_by_external_id(self, db: Session, external_id: str) -> VehicleEvent | None:
        return db.scalar(select(VehicleEvent).where(VehicleEvent.external_id == external_id))

    def _find_by_capture_key(
        self,
        db: Session,
        *,
        camera_id: UUID,
        captured_at: datetime,
        normalized_plate: str | None,
    ) -> VehicleEvent | None:
        if normalized_plate is None:
            return None

        return db.scalar(
            select(VehicleEvent).where(
                VehicleEvent.camera_id == camera_id,
                VehicleEvent.captured_at == captured_at,
                VehicleEvent.normalized_plate == normalized_plate,
            )
        )

    def _resolve_authorization(
        self,
        db: Session,
        normalized_plate: str | None,
    ) -> AuthorizationStatus:
        if not normalized_plate:
            return AuthorizationStatus.UNKNOWN

        authorized = db.scalar(
            select(AuthorizedVehicle).where(
                AuthorizedVehicle.normalized_plate == normalized_plate,
                AuthorizedVehicle.active.is_(True),
            )
        )
        if authorized is not None:
            return AuthorizationStatus.AUTHORIZED
        return AuthorizationStatus.VISITOR

    def _upsert_vehicle_profile(
        self,
        db: Session,
        *,
        normalized_plate: str | None,
        captured_at: datetime,
    ) -> VehicleProfile:
        authorized_vehicle_id = None
        if normalized_plate:
            authorized = db.scalar(
                select(AuthorizedVehicle).where(
                    AuthorizedVehicle.normalized_plate == normalized_plate,
                    AuthorizedVehicle.active.is_(True),
                )
            )
            if authorized is not None:
                authorized_vehicle_id = authorized.id

            profile = db.scalar(
                select(VehicleProfile).where(VehicleProfile.normalized_plate == normalized_plate)
            )
            if profile is not None:
                if captured_at < profile.first_seen_at:
                    profile.first_seen_at = captured_at
                if captured_at > profile.last_seen_at:
                    profile.last_seen_at = captured_at
                if authorized_vehicle_id is not None:
                    profile.authorized_vehicle_id = authorized_vehicle_id
                return profile

            profile = VehicleProfile(
                normalized_plate=normalized_plate,
                first_seen_at=captured_at,
                last_seen_at=captured_at,
                authorized_vehicle_id=authorized_vehicle_id,
            )
            db.add(profile)
            db.flush()
            return profile

        profile = VehicleProfile(
            normalized_plate=None,
            first_seen_at=captured_at,
            last_seen_at=captured_at,
            authorized_vehicle_id=None,
        )
        db.add(profile)
        db.flush()
        return profile


def _to_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        raise IngestError(
            "timestamp must include timezone information",
            code="invalid_timestamp",
        )
    return timestamp.astimezone(UTC)


def _pending_image_refs(image_urls: list[str]) -> list[dict[str, str]]:
    return [{"source_url": url, "status": "pending"} for url in image_urls]


def _payloads_match(stored: dict, incoming: dict) -> bool:
    return stored == incoming
