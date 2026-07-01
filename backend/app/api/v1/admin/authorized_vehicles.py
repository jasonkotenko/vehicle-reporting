"""Admin authorized vehicle management routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.db.session import get_db
from app.models.enums import VehicleCategory
from app.schemas.authorized_vehicle import (
    AuthorizedVehicleCreate,
    AuthorizedVehicleResponse,
    AuthorizedVehicleUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.authorized_vehicles import AuthorizedVehicleService

router = APIRouter(prefix="/authorized-vehicles", tags=["admin-authorized-vehicles"])


@router.get("", response_model=PaginatedResponse[AuthorizedVehicleResponse])
def list_authorized_vehicles(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    active: bool | None = None,
    category: VehicleCategory | None = None,
    plate: str | None = None,
) -> PaginatedResponse[AuthorizedVehicleResponse]:
    return AuthorizedVehicleService().list_authorized_vehicles(
        db,
        page=page,
        page_size=page_size,
        active=active,
        category=category,
        plate=plate,
    )


@router.post("", response_model=AuthorizedVehicleResponse, status_code=201)
def create_authorized_vehicle(
    payload: AuthorizedVehicleCreate,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> AuthorizedVehicleResponse:
    return AuthorizedVehicleService().create_authorized_vehicle(db, payload)


@router.get("/{record_id}", response_model=AuthorizedVehicleResponse)
def get_authorized_vehicle(
    record_id: UUID,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> AuthorizedVehicleResponse:
    return AuthorizedVehicleService().get_authorized_vehicle(db, record_id)


@router.patch("/{record_id}", response_model=AuthorizedVehicleResponse)
def update_authorized_vehicle(
    record_id: UUID,
    payload: AuthorizedVehicleUpdate,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> AuthorizedVehicleResponse:
    return AuthorizedVehicleService().update_authorized_vehicle(db, record_id, payload)
