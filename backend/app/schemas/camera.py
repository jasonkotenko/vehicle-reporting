"""Camera admin API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ZoneType


class CameraCreate(BaseModel):
    camera_id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=255)
    zone_type: ZoneType


class CameraUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    zone_type: ZoneType | None = None
    active: bool | None = None


class CameraResponse(BaseModel):
    id: UUID
    camera_id: str
    label: str
    zone_type: ZoneType
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
