"""Historical report routes (admin)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.api.export_responses import build_export_response, parse_export_format
from app.core.query import parse_time_range
from app.db.session import get_db
from app.models.enums import TripStatus
from app.schemas.exports import ExportFilters, ReportType
from app.services.read_api import ReadApiService

router = APIRouter(prefix="/reports", tags=["reports"])


def _export_filters(
    *,
    plate: str | None,
    from_: str | None,
    to: str | None,
    camera_ids: list[str] | None = None,
    status: TripStatus | None = None,
) -> ExportFilters:
    return ExportFilters(
        time_range=parse_time_range(from_, to),
        plate=plate,
        camera_ids=camera_ids,
        status=status,
        from_raw=from_,
        to_raw=to,
    )


@router.get("/entries")
def report_entries(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    plate: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
    format: str | None = Query(None, description="Export format: csv or pdf"),
):
    export_format = parse_export_format(format)
    filters = _export_filters(plate=plate, from_=from_, to=to)
    if export_format:
        return build_export_response(
            report_type=ReportType.ENTRIES,
            export_format=export_format,
            db=db,
            filters=filters,
        )
    return ReadApiService().report_entries(
        db,
        page=page,
        page_size=page_size,
        plate=plate,
        time_range=filters.time_range,
    )


@router.get("/exits")
def report_exits(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    plate: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
    format: str | None = Query(None, description="Export format: csv or pdf"),
):
    export_format = parse_export_format(format)
    filters = _export_filters(plate=plate, from_=from_, to=to)
    if export_format:
        return build_export_response(
            report_type=ReportType.EXITS,
            export_format=export_format,
            db=db,
            filters=filters,
        )
    return ReadApiService().report_exits(
        db,
        page=page,
        page_size=page_size,
        plate=plate,
        time_range=filters.time_range,
    )


@router.get("/transits")
def report_transits(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    camera_ids: list[str] = Query(default=[]),
    plate: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
    format: str | None = Query(None, description="Export format: csv or pdf"),
):
    export_format = parse_export_format(format)
    filters = _export_filters(plate=plate, from_=from_, to=to, camera_ids=camera_ids)
    if export_format:
        return build_export_response(
            report_type=ReportType.TRANSITS,
            export_format=export_format,
            db=db,
            filters=filters,
        )
    return ReadApiService().report_transits(
        db,
        page=page,
        page_size=page_size,
        camera_ids=camera_ids,
        plate=plate,
        time_range=filters.time_range,
    )


@router.get("/trips")
def report_trips(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: TripStatus | None = None,
    plate: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
    format: str | None = Query(None, description="Export format: csv or pdf"),
):
    export_format = parse_export_format(format)
    filters = _export_filters(plate=plate, from_=from_, to=to, status=status)
    if export_format:
        return build_export_response(
            report_type=ReportType.TRIPS,
            export_format=export_format,
            db=db,
            filters=filters,
        )
    return ReadApiService().report_trips(
        db,
        page=page,
        page_size=page_size,
        status=status,
        plate=plate,
        time_range=filters.time_range,
    )
