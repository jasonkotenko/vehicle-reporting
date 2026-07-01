"""Ingest-specific exceptions."""

from __future__ import annotations


class IngestError(Exception):
    def __init__(self, detail: str, *, code: str, status_code: int = 422) -> None:
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)
