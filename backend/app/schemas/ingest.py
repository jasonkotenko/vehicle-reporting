"""Ingest API request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PlateStatus


class IngestEventRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    external_id: str | None = None
    camera_id: str = Field(min_length=1, max_length=64)
    timestamp: datetime
    license_plate: str | None = None
    plate_status: PlateStatus
    image_urls: list[str] = Field(min_length=1)

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, urls: list[str]) -> list[str]:
        for url in urls:
            if not url.startswith(("http://", "https://")):
                raise ValueError("image_urls must contain HTTP or HTTPS URLs")
        return urls


class IngestEventResponse(BaseModel):
    event_id: UUID
    vehicle_profile_id: UUID
