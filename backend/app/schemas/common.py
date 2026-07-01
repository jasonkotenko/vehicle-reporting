"""Shared response schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
  items: list[T]
  total: int
  page: int = Field(ge=1)
  page_size: int = Field(ge=1, le=200)


class ErrorResponse(BaseModel):
  type: str = "about:blank"
  title: str
  status: int
  detail: str
  code: str
