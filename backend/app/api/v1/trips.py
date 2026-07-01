"""Trip read routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import OperatorUser
from app.core.query import parse_time_range
from app.db.session import get_db
from app.models.enums import TripStatus
from app.schemas.common import PaginatedResponse
from app.schemas.read_api import TripDetailResponse, TripSummary
from app.services.read_api import ReadApiService

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("", response_model=PaginatedResponse[TripSummary])
def list_trips(
    _: OperatorUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: TripStatus | None = None,
    plate: str | None = None,
    camera_id: str | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
) -> PaginatedResponse[TripSummary]:
    return ReadApiService().list_trips(
        db,
        page=page,
        page_size=page_size,
        status=status,
        plate=plate,
        camera_id=camera_id,
        time_range=parse_time_range(from_, to),
    )


@router.get("/{trip_id}", response_model=TripDetailResponse)
def get_trip(
    trip_id: UUID,
    _: OperatorUser,
    db: Session = Depends(get_db),
) -> TripDetailResponse:
    return ReadApiService().get_trip(db, trip_id)
