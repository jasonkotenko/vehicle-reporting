"""Historical report routes (admin)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.core.query import parse_time_range
from app.db.session import get_db
from app.models.enums import TripStatus
from app.schemas.common import PaginatedResponse
from app.schemas.read_api import ReportEventRow, TripSummary
from app.services.read_api import ReadApiService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/entries", response_model=PaginatedResponse[ReportEventRow])
def report_entries(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    plate: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
) -> PaginatedResponse[ReportEventRow]:
    return ReadApiService().report_entries(
        db,
        page=page,
        page_size=page_size,
        plate=plate,
        time_range=parse_time_range(from_, to),
    )


@router.get("/exits", response_model=PaginatedResponse[ReportEventRow])
def report_exits(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    plate: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
) -> PaginatedResponse[ReportEventRow]:
    return ReadApiService().report_exits(
        db,
        page=page,
        page_size=page_size,
        plate=plate,
        time_range=parse_time_range(from_, to),
    )


@router.get("/transits", response_model=PaginatedResponse[ReportEventRow])
def report_transits(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    camera_ids: list[str] = Query(default=[]),
    plate: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
) -> PaginatedResponse[ReportEventRow]:
    return ReadApiService().report_transits(
        db,
        page=page,
        page_size=page_size,
        camera_ids=camera_ids,
        plate=plate,
        time_range=parse_time_range(from_, to),
    )


@router.get("/trips", response_model=PaginatedResponse[TripSummary])
def report_trips(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: TripStatus | None = None,
    plate: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
) -> PaginatedResponse[TripSummary]:
    return ReadApiService().report_trips(
        db,
        page=page,
        page_size=page_size,
        status=status,
        plate=plate,
        time_range=parse_time_range(from_, to),
    )
