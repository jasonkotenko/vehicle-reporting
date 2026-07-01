"""Vehicle event read routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import OperatorUser
from app.core.query import parse_time_range
from app.db.session import get_db
from app.models.enums import AuthorizationStatus, PlateStatus
from app.schemas.common import PaginatedResponse
from app.schemas.read_api import EventDetailResponse, EventSummary
from app.services.read_api import ReadApiService

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=PaginatedResponse[EventSummary])
def list_events(
    _: OperatorUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    plate: str | None = None,
    camera_id: str | None = None,
    plate_status: PlateStatus | None = None,
    authorization_status: AuthorizationStatus | None = None,
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
) -> PaginatedResponse[EventSummary]:
    return ReadApiService().list_events(
        db,
        page=page,
        page_size=page_size,
        plate=plate,
        camera_id=camera_id,
        plate_status=plate_status,
        authorization_status=authorization_status,
        time_range=parse_time_range(from_, to),
    )


@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(
    event_id: UUID,
    _: OperatorUser,
    db: Session = Depends(get_db),
) -> EventDetailResponse:
    return ReadApiService().get_event(db, event_id)
