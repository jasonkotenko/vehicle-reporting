"""Pydantic schemas for API v1."""

from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.config import AppConfigResponse
from app.schemas.health import HealthResponse

__all__ = [
    "AppConfigResponse",
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
]
