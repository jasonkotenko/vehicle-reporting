"""Public application configuration exposed to clients."""

from pydantic import BaseModel, Field


class AppConfigResponse(BaseModel):
  display_timezone: str = Field(
    description="IANA timezone used for UI display and report boundaries",
    examples=["Asia/Manila"],
  )
