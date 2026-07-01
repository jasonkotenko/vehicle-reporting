"""Immutable vehicle detection events from CV ingest."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import AuthorizationStatus, PlateStatus


class VehicleEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "vehicle_events"
    __table_args__ = (
        Index("ix_vehicle_events_normalized_plate_captured_at", "normalized_plate", "captured_at"),
        Index("ix_vehicle_events_camera_id_captured_at", "camera_id", "captured_at"),
        Index("ix_vehicle_events_captured_at", "captured_at"),
        Index("ix_vehicle_events_vehicle_profile_id_captured_at", "vehicle_profile_id", "captured_at"),
        Index(
            "uq_vehicle_events_external_id",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    camera_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cameras.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vehicle_profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_plate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    normalized_plate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    effective_plate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    plate_status: Mapped[PlateStatus] = mapped_column(
        Enum(PlateStatus, name="plate_status"),
        nullable=False,
    )
    image_refs: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    authorization_status: Mapped[AuthorizationStatus] = mapped_column(
        Enum(AuthorizationStatus, name="authorization_status"),
        nullable=False,
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
