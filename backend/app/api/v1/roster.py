"""Active roster read route."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import OperatorUser
from app.api.export_responses import build_export_response, parse_export_format
from app.core.query import TimeRange
from app.db.session import get_db
from app.schemas.exports import ExportFilters, ReportType
from app.schemas.read_api import RosterItem
from app.services.read_api import ReadApiService

router = APIRouter(prefix="/roster", tags=["roster"])


@router.get("")
def get_roster(
    _: OperatorUser,
    db: Session = Depends(get_db),
    format: str | None = Query(None, description="Export format: csv or pdf"),
):
    export_format = parse_export_format(format)
    if export_format:
        filters = ExportFilters(time_range=TimeRange(start=None, end=None))
        return build_export_response(
            report_type=ReportType.ROSTER,
            export_format=export_format,
            db=db,
            filters=filters,
        )
    return ReadApiService().get_roster(db)
