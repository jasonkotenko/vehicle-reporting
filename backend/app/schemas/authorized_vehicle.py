"""Authorized vehicle admin API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import VehicleCategory


class AuthorizedVehicleCreate(BaseModel):
    plate: str = Field(min_length=1, max_length=32)
    category: VehicleCategory
    owner_name: str = Field(min_length=1, max_length=255)
    owner_address: str = Field(min_length=1, max_length=512)


class AuthorizedVehicleUpdate(BaseModel):
    plate: str | None = Field(default=None, min_length=1, max_length=32)
    category: VehicleCategory | None = None
    owner_name: str | None = Field(default=None, min_length=1, max_length=255)
    owner_address: str | None = Field(default=None, min_length=1, max_length=512)
    active: bool | None = None


class AuthorizedVehicleResponse(BaseModel):
    id: UUID
    plate: str
    normalized_plate: str
    category: VehicleCategory
    owner_name: str
    owner_address: str
    active: bool
    created_at: datetime
    updated_at: datetime
    vehicle_profile_id: UUID | None = None

    model_config = {"from_attributes": True}
