"""Operator plate correction schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import PlateStatus
from app.schemas.read_api import EntityLinks


class EventGalleryResponse(BaseModel):
    event_id: UUID
    image_refs: list
    plate_status: PlateStatus
    raw_plate: str | None
    effective_plate: str | None
    links: EntityLinks


class CorrectPlateRequest(BaseModel):
    new_plate: str = Field(min_length=1, max_length=32)
    note: str | None = Field(default=None, max_length=500)


class CorrectPlateResponse(BaseModel):
    event_id: UUID
    vehicle_profile_id: UUID
    effective_plate: str
    audit_id: UUID
    links: EntityLinks


class AuditCorrectionSummary(BaseModel):
    id: UUID
    vehicle_event_id: UUID
    corrected_at: datetime
    corrected_by_display_name: str
    original_raw_plate: str | None
    original_effective_plate: str | None
    new_plate: str
    links: EntityLinks


class AuditCorrectionDetail(AuditCorrectionSummary):
    original_raw_payload: dict
    image_refs: list
