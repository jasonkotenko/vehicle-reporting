"""SQLAlchemy ORM models."""

from app.models.authorized_vehicle import AuthorizedVehicle
from app.models.base import Base
from app.models.camera import Camera
from app.models.plate_correction_audit import PlateCorrectionAudit
from app.models.trip import Trip
from app.models.trip_event import TripEvent
from app.models.user import User
from app.models.vehicle_event import VehicleEvent
from app.models.vehicle_profile import VehicleProfile

__all__ = [
    "AuthorizedVehicle",
    "Base",
    "Camera",
    "PlateCorrectionAudit",
    "Trip",
    "TripEvent",
    "User",
    "VehicleEvent",
    "VehicleProfile",
]
