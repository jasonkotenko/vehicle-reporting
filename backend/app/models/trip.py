"""Computed vehicle stay within the village."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import TripStatus


class Trip(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "trips"

    vehicle_profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[TripStatus] = mapped_column(Enum(TripStatus, name="trip_status"), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entry_event_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    exit_event_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_events.id", ondelete="SET NULL"),
        nullable=True,
    )
