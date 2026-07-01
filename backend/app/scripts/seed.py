"""Development database seed data."""

from __future__ import annotations

import os

from sqlalchemy import select

from app.core.plates import normalize_plate
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import AuthorizedVehicle, Camera, User
from app.models.enums import UserRole, VehicleCategory, ZoneType


def seed() -> None:
    admin_password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "admin")
    db = SessionLocal()
    try:
        if db.scalar(select(User).limit(1)) is None:
            db.add(
                User(
                    username="admin",
                    password_hash=hash_password(admin_password),
                    display_name="Administrator",
                    role=UserRole.ADMIN,
                )
            )

        if db.scalar(select(Camera).limit(1)) is None:
            db.add_all(
                [
                    Camera(
                        camera_id="CAM-MAIN-ENTRY",
                        label="Main Gate - Entry",
                        zone_type=ZoneType.ENTRY,
                    ),
                    Camera(
                        camera_id="CAM-MAIN-EXIT",
                        label="Main Gate - Exit",
                        zone_type=ZoneType.EXIT,
                    ),
                    Camera(
                        camera_id="CAM-INT-01",
                        label="Intersection 1",
                        zone_type=ZoneType.INTERNAL,
                    ),
                ]
            )

        if db.scalar(select(AuthorizedVehicle).limit(1)) is None:
            db.add(
                AuthorizedVehicle(
                    normalized_plate=normalize_plate("ABC 1234") or "ABC1234",
                    category=VehicleCategory.RESIDENT,
                    owner_name="Juan Dela Cruz",
                    owner_address="Block 12 Lot 5, Maple Street",
                )
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seed data applied.")
