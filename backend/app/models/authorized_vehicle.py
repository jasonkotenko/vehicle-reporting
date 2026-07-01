"""Authorized resident, staff, and service vehicles."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import VehicleCategory


class AuthorizedVehicle(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "authorized_vehicles"

    normalized_plate: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    category: Mapped[VehicleCategory] = mapped_column(
        Enum(VehicleCategory, name="vehicle_category"),
        nullable=False,
    )
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_address: Mapped[str] = mapped_column(String(512), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
