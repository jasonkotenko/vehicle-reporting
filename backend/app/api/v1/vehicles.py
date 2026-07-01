"""Vehicle profile read routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import OperatorUser
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.read_api import EventSummary, TripSummary, VehicleProfileDetail, VehicleSearchItem
from app.services.read_api import ReadApiService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=PaginatedResponse[VehicleSearchItem])
def search_vehicles(
    _: OperatorUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    plate: str | None = None,
) -> PaginatedResponse[VehicleSearchItem]:
    return ReadApiService().search_vehicles(db, page=page, page_size=page_size, plate=plate)


@router.get("/{vehicle_id}", response_model=VehicleProfileDetail)
def get_vehicle(
    vehicle_id: UUID,
    _: OperatorUser,
    db: Session = Depends(get_db),
) -> VehicleProfileDetail:
    return ReadApiService().get_vehicle(db, vehicle_id)


@router.get("/{vehicle_id}/events", response_model=PaginatedResponse[EventSummary])
def list_vehicle_events(
    vehicle_id: UUID,
    _: OperatorUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[EventSummary]:
    return ReadApiService().list_vehicle_events(
        db, vehicle_id, page=page, page_size=page_size
    )


@router.get("/{vehicle_id}/trips", response_model=PaginatedResponse[TripSummary])
def list_vehicle_trips(
    vehicle_id: UUID,
    _: OperatorUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[TripSummary]:
    return ReadApiService().list_vehicle_trips(db, vehicle_id, page=page, page_size=page_size)
