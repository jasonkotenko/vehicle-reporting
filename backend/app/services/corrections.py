"""Operator plate correction and audit trail."""

from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.plates import normalize_plate
from app.core.query import link_event
from app.models import PlateCorrectionAudit, User, VehicleEvent
from app.schemas.common import PaginatedResponse
from app.schemas.corrections import (
    AuditCorrectionDetail,
    AuditCorrectionSummary,
    CorrectPlateResponse,
    EventGalleryResponse,
)
from app.schemas.read_api import EntityLinks
from app.services.correction_errors import CorrectionError
from app.services.image_tokens import enrich_image_refs
from app.services.ingest import IngestService
from app.services.read_errors import ReadError
from app.services.trips import recompute_trips_for_profile


class CorrectionService:
    def get_event_gallery(self, db: Session, event_id: UUID) -> EventGalleryResponse:
        event = db.get(VehicleEvent, event_id)
        if event is None:
            raise ReadError("Event not found", code="event_not_found")

        return EventGalleryResponse(
            event_id=event.id,
            image_refs=enrich_image_refs(deepcopy(event.image_refs)),
            plate_status=event.plate_status,
            raw_plate=event.raw_plate,
            effective_plate=event.effective_plate,
            links=EntityLinks(self=link_event(event.id)),
        )

    def correct_plate(
        self,
        db: Session,
        event_id: UUID,
        *,
        new_plate: str,
        corrected_by_user_id: UUID,
    ) -> CorrectPlateResponse:
        event = db.get(VehicleEvent, event_id)
        if event is None:
            raise ReadError("Event not found", code="event_not_found")

        new_normalized = normalize_plate(new_plate)
        if not new_normalized:
            raise CorrectionError(
                "Plate must contain alphanumeric characters",
                code="invalid_plate",
            )

        current_normalized = normalize_plate(event.effective_plate) or event.normalized_plate
        if new_normalized == current_normalized:
            raise CorrectionError("Plate is unchanged", code="unchanged_plate")

        original_payload = deepcopy(event.raw_payload)
        original_image_refs = deepcopy(event.image_refs)
        old_profile_id = event.vehicle_profile_id

        audit = PlateCorrectionAudit(
            vehicle_event_id=event.id,
            corrected_by_user_id=corrected_by_user_id,
            original_raw_plate=event.raw_plate,
            original_effective_plate=event.effective_plate,
            new_plate=new_normalized,
            original_raw_payload=original_payload,
            image_refs=original_image_refs,
        )
        db.add(audit)

        ingest = IngestService()
        profile = ingest.link_profile_for_plate(
            db,
            normalized_plate=new_normalized,
            captured_at=event.captured_at,
        )

        event.effective_plate = new_normalized
        event.normalized_plate = new_normalized
        event.vehicle_profile_id = profile.id
        event.authorization_status = ingest.authorization_for_plate(db, new_normalized)

        db.flush()

        recompute_trips_for_profile(db, old_profile_id)
        if profile.id != old_profile_id:
            recompute_trips_for_profile(db, profile.id)

        db.commit()
        db.refresh(event)
        db.refresh(audit)

        return CorrectPlateResponse(
            event_id=event.id,
            vehicle_profile_id=event.vehicle_profile_id,
            effective_plate=event.effective_plate,
            audit_id=audit.id,
            links=EntityLinks(
                self=link_event(event.id),
                vehicle=f"/api/v1/vehicles/{event.vehicle_profile_id}",
            ),
        )


class AuditService:
    def list_corrections(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[AuditCorrectionSummary]:
        query = (
            select(PlateCorrectionAudit, User)
            .join(User, PlateCorrectionAudit.corrected_by_user_id == User.id)
            .order_by(PlateCorrectionAudit.corrected_at.desc(), PlateCorrectionAudit.id.desc())
        )
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = db.execute(query.offset((page - 1) * page_size).limit(page_size)).all()

        return PaginatedResponse(
            items=[self._to_summary(audit, user) for audit, user in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_correction(self, db: Session, audit_id: UUID) -> AuditCorrectionDetail:
        row = db.execute(
            select(PlateCorrectionAudit, User)
            .join(User, PlateCorrectionAudit.corrected_by_user_id == User.id)
            .where(PlateCorrectionAudit.id == audit_id)
        ).one_or_none()
        if row is None:
            raise CorrectionError(
                "Correction audit not found",
                code="audit_not_found",
                status_code=404,
            )

        audit, user = row
        summary = self._to_summary(audit, user)
        return AuditCorrectionDetail(
            **summary.model_dump(),
            original_raw_payload=audit.original_raw_payload,
            image_refs=audit.image_refs,
        )

    def _to_summary(self, audit: PlateCorrectionAudit, user: User) -> AuditCorrectionSummary:
        return AuditCorrectionSummary(
            id=audit.id,
            vehicle_event_id=audit.vehicle_event_id,
            corrected_at=audit.corrected_at,
            corrected_by_display_name=user.display_name,
            original_raw_plate=audit.original_raw_plate,
            original_effective_plate=audit.original_effective_plate,
            new_plate=audit.new_plate,
            links=EntityLinks(
                self=f"/api/v1/admin/audit/corrections/{audit.id}",
                event=link_event(audit.vehicle_event_id),
            ),
        )
