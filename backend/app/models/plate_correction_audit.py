"""Immutable audit log for operator plate corrections."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class PlateCorrectionAudit(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "plate_correction_audit"

    vehicle_event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    corrected_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    original_raw_plate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    original_effective_plate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_plate: Mapped[str] = mapped_column(String(32), nullable=False)
    original_raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    image_refs: Mapped[list] = mapped_column(JSONB, nullable=False)
