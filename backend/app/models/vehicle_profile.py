"""Vehicle profile aggregated by license plate."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class VehicleProfile(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "vehicle_profiles"

    normalized_plate: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    authorized_vehicle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("authorized_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
