"""Shared API error handling."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.admin_errors import AdminError
from app.services.correction_errors import CorrectionError
from app.services.ingest_errors import IngestError
from app.services.read_errors import ReadError


def _error_body(
    *,
    status: int,
    detail: str,
    code: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": detail,
        "status": status,
        "detail": detail,
        "code": code,
    }
    if extra:
        body.update(extra)
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        code = "http_error"
        if isinstance(exc.detail, str) and exc.detail:
            code = exc.detail.lower().replace(" ", "_")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(status=exc.status_code, detail=str(exc.detail), code=code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(
                status=422,
                detail="Request validation failed",
                code="validation_error",
                extra={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(IngestError)
    async def ingest_exception_handler(
        _request: Request,
        exc: IngestError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(status=exc.status_code, detail=exc.detail, code=exc.code),
        )

    @app.exception_handler(AdminError)
    async def admin_exception_handler(
        _request: Request,
        exc: AdminError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(status=exc.status_code, detail=exc.detail, code=exc.code),
        )

    @app.exception_handler(ReadError)
    async def read_exception_handler(
        _request: Request,
        exc: ReadError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(status=exc.status_code, detail=exc.detail, code=exc.code),
        )

    @app.exception_handler(CorrectionError)
    async def correction_exception_handler(
        _request: Request,
        exc: CorrectionError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(status=exc.status_code, detail=exc.detail, code=exc.code),
        )
