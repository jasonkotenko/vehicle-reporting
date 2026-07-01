"""Plate correction domain errors."""

from __future__ import annotations


class CorrectionError(Exception):
    def __init__(self, detail: str, *, code: str, status_code: int = 400) -> None:
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)
