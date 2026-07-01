"""Shared helpers for CSV/PDF export responses."""

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.schemas.exports import ExportFilters, ReportType
from app.services.exports import ExportService

ExportFormat = Literal["csv", "pdf"]


def build_export_response(
    *,
    report_type: ReportType,
    export_format: ExportFormat,
    db: Session,
    filters: ExportFilters,
) -> StreamingResponse | Response:
    service = ExportService()
    filename = service.filename(report_type, export_format)

    if export_format == "csv":
        return StreamingResponse(
            service.export_csv(report_type, db, filters),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    pdf_bytes = service.export_pdf(report_type, db, filters)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def parse_export_format(format: str | None) -> ExportFormat | None:
    if format is None:
        return None
    if format not in {"csv", "pdf"}:
        raise HTTPException(status_code=400, detail="format must be csv or pdf")
    return format  # type: ignore[return-value]
