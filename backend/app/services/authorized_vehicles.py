"""Authorized vehicle directory management."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.plates import normalize_plate
from app.models import AuthorizedVehicle, VehicleProfile
from app.models.enums import VehicleCategory
from app.schemas.authorized_vehicle import (
    AuthorizedVehicleCreate,
    AuthorizedVehicleResponse,
    AuthorizedVehicleUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.admin_errors import AdminError


class AuthorizedVehicleService:
    def list_authorized_vehicles(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        active: bool | None,
        category: VehicleCategory | None,
        plate: str | None,
    ) -> PaginatedResponse[AuthorizedVehicleResponse]:
        query = select(AuthorizedVehicle)
        if active is not None:
            query = query.where(AuthorizedVehicle.active.is_(active))
        if category is not None:
            query = query.where(AuthorizedVehicle.category == category)
        if plate:
            normalized_search = normalize_plate(plate)
            if normalized_search:
                query = query.where(AuthorizedVehicle.normalized_plate.ilike(f"%{normalized_search}%"))

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = db.scalars(
            query.order_by(AuthorizedVehicle.normalized_plate)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedResponse(
            items=[self._to_response(db, item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_authorized_vehicle(self, db: Session, record_id: UUID) -> AuthorizedVehicleResponse:
        record = db.get(AuthorizedVehicle, record_id)
        if record is None:
            raise AdminError(
                "Authorized vehicle not found",
                code="authorized_vehicle_not_found",
                status_code=404,
            )
        return self._to_response(db, record)

    def create_authorized_vehicle(
        self,
        db: Session,
        payload: AuthorizedVehicleCreate,
    ) -> AuthorizedVehicleResponse:
        normalized_plate = self._normalize_required_plate(payload.plate)
        existing = db.scalar(
            select(AuthorizedVehicle).where(AuthorizedVehicle.normalized_plate == normalized_plate)
        )
        if existing is not None:
            raise AdminError(
                f"Authorized plate already exists: {normalized_plate}",
                code="duplicate_plate",
                status_code=409,
            )

        record = AuthorizedVehicle(
            normalized_plate=normalized_plate,
            category=payload.category,
            owner_name=payload.owner_name,
            owner_address=payload.owner_address,
        )
        db.add(record)
        db.flush()
        self._relink_matching_profiles(db, record)
        db.commit()
        db.refresh(record)
        return self._to_response(db, record)

    def update_authorized_vehicle(
        self,
        db: Session,
        record_id: UUID,
        payload: AuthorizedVehicleUpdate,
    ) -> AuthorizedVehicleResponse:
        record = db.get(AuthorizedVehicle, record_id)
        if record is None:
            raise AdminError(
                "Authorized vehicle not found",
                code="authorized_vehicle_not_found",
                status_code=404,
            )

        updates = payload.model_dump(exclude_unset=True)
        if "plate" in updates:
            normalized_plate = self._normalize_required_plate(updates.pop("plate"))
            duplicate = db.scalar(
                select(AuthorizedVehicle).where(
                    AuthorizedVehicle.normalized_plate == normalized_plate,
                    AuthorizedVehicle.id != record.id,
                )
            )
            if duplicate is not None:
                raise AdminError(
                    f"Authorized plate already exists: {normalized_plate}",
                    code="duplicate_plate",
                    status_code=409,
                )
            old_normalized_plate = record.normalized_plate
            record.normalized_plate = normalized_plate
            self._clear_profile_links_for_plate(db, old_normalized_plate)

        for field, value in updates.items():
            setattr(record, field, value)

        self._relink_matching_profiles(db, record)
        db.commit()
        db.refresh(record)
        return self._to_response(db, record)

    def _normalize_required_plate(self, plate: str) -> str:
        normalized = normalize_plate(plate)
        if not normalized:
            raise AdminError("Plate must contain alphanumeric characters", code="invalid_plate")
        return normalized

    def _relink_matching_profiles(self, db: Session, record: AuthorizedVehicle) -> None:
        profiles = db.scalars(
            select(VehicleProfile).where(VehicleProfile.normalized_plate == record.normalized_plate)
        ).all()
        for profile in profiles:
            profile.authorized_vehicle_id = record.id if record.active else None

    def _clear_profile_links_for_plate(self, db: Session, normalized_plate: str) -> None:
        profiles = db.scalars(
            select(VehicleProfile).where(VehicleProfile.normalized_plate == normalized_plate)
        ).all()
        for profile in profiles:
            profile.authorized_vehicle_id = None

    def _to_response(self, db: Session, record: AuthorizedVehicle) -> AuthorizedVehicleResponse:
        profile = db.scalar(
            select(VehicleProfile).where(VehicleProfile.normalized_plate == record.normalized_plate)
        )
        return AuthorizedVehicleResponse(
            id=record.id,
            plate=record.normalized_plate,
            normalized_plate=record.normalized_plate,
            category=record.category,
            owner_name=record.owner_name,
            owner_address=record.owner_address,
            active=record.active,
            created_at=record.created_at,
            updated_at=record.updated_at,
            vehicle_profile_id=profile.id if profile else None,
        )
