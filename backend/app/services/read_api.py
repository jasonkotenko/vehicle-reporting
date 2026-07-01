"""Query and reporting read APIs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.query import (
    TimeRange,
    apply_time_range,
    link_authorized,
    link_event,
    link_trip,
    link_vehicle,
    normalize_plate_query,
)
from app.models import Camera, Trip, TripEvent, VehicleEvent, VehicleProfile
from app.models.enums import AuthorizationStatus, PlateStatus, TripStatus, ZoneType
from app.schemas.common import PaginatedResponse
from app.schemas.read_api import (
    EntityLinks,
    EventDetailResponse,
    EventSummary,
    ReportEventRow,
    RosterItem,
    TripDetailResponse,
    TripEventView,
    TripSummary,
    VehicleProfileBrief,
    VehicleProfileDetail,
    VehicleSearchItem,
)
from app.services.read_errors import ReadError
from app.services.trips import get_active_roster, get_trip_with_events


class ReadApiService:
    def search_vehicles(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        plate: str | None,
    ) -> PaginatedResponse[VehicleSearchItem]:
        query = select(VehicleProfile)
        normalized = normalize_plate_query(plate)
        if normalized:
            query = query.where(VehicleProfile.normalized_plate.ilike(f"%{normalized}%"))

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        profiles = db.scalars(
            query.order_by(VehicleProfile.last_seen_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedResponse(
            items=[self._vehicle_search_item(profile) for profile in profiles],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_vehicle(self, db: Session, vehicle_id: UUID) -> VehicleProfileDetail:
        profile = db.get(VehicleProfile, vehicle_id)
        if profile is None:
            raise ReadError("Vehicle profile not found", code="vehicle_not_found")

        event_count = db.scalar(
            select(func.count()).where(VehicleEvent.vehicle_profile_id == vehicle_id)
        ) or 0
        trip_count = db.scalar(select(func.count()).where(Trip.vehicle_profile_id == vehicle_id)) or 0

        links = EntityLinks(
            self=link_vehicle(profile.id),
            authorized=link_authorized(profile.authorized_vehicle_id)
            if profile.authorized_vehicle_id
            else None,
        )
        return VehicleProfileDetail(
            id=profile.id,
            plate=profile.normalized_plate,
            normalized_plate=profile.normalized_plate,
            first_seen_at=profile.first_seen_at,
            last_seen_at=profile.last_seen_at,
            event_count=event_count,
            trip_count=trip_count,
            authorized_vehicle_id=profile.authorized_vehicle_id,
            links=links,
        )

    def list_vehicle_events(
        self,
        db: Session,
        vehicle_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[EventSummary]:
        profile = db.get(VehicleProfile, vehicle_id)
        if profile is None:
            raise ReadError("Vehicle profile not found", code="vehicle_not_found")

        query = (
            select(VehicleEvent, Camera)
            .join(Camera, VehicleEvent.camera_id == Camera.id)
            .where(VehicleEvent.vehicle_profile_id == vehicle_id)
        )
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = db.execute(
            query.order_by(VehicleEvent.captured_at.desc(), VehicleEvent.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedResponse(
            items=[self._event_summary(event, camera) for event, camera in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_vehicle_trips(
        self,
        db: Session,
        vehicle_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[TripSummary]:
        profile = db.get(VehicleProfile, vehicle_id)
        if profile is None:
            raise ReadError("Vehicle profile not found", code="vehicle_not_found")

        query = select(Trip).where(Trip.vehicle_profile_id == vehicle_id)
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        trips = db.scalars(
            query.order_by(Trip.started_at.desc().nullslast(), Trip.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedResponse(
            items=[self._trip_summary(db, trip, profile) for trip in trips],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_events(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        plate: str | None,
        camera_id: str | None,
        plate_status: PlateStatus | None,
        authorization_status: AuthorizationStatus | None,
        time_range: TimeRange,
    ) -> PaginatedResponse[EventSummary]:
        query = select(VehicleEvent, Camera).join(Camera, VehicleEvent.camera_id == Camera.id)

        normalized = normalize_plate_query(plate)
        if normalized:
            query = query.where(VehicleEvent.normalized_plate.ilike(f"%{normalized}%"))
        if camera_id:
            query = query.where(Camera.camera_id == camera_id)
        if plate_status is not None:
            query = query.where(VehicleEvent.plate_status == plate_status)
        if authorization_status is not None:
            query = query.where(VehicleEvent.authorization_status == authorization_status)
        query = apply_time_range(query, VehicleEvent.captured_at, time_range)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = db.execute(
            query.order_by(VehicleEvent.captured_at.desc(), VehicleEvent.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedResponse(
            items=[self._event_summary(event, camera) for event, camera in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_event(self, db: Session, event_id: UUID) -> EventDetailResponse:
        row = db.execute(
            select(VehicleEvent, Camera)
            .join(Camera, VehicleEvent.camera_id == Camera.id)
            .where(VehicleEvent.id == event_id)
        ).one_or_none()
        if row is None:
            raise ReadError("Event not found", code="event_not_found")

        event, camera = row
        trip_id = db.scalar(
            select(TripEvent.trip_id).where(TripEvent.vehicle_event_id == event_id)
        )
        summary = self._event_summary(event, camera)
        return EventDetailResponse(
            id=summary.id,
            captured_at=summary.captured_at,
            plate=summary.plate,
            effective_plate=summary.effective_plate,
            plate_status=summary.plate_status,
            authorization_status=summary.authorization_status,
            camera_id=summary.camera_id,
            camera_label=summary.camera_label,
            zone_type=summary.zone_type,
            vehicle_profile_id=event.vehicle_profile_id,
            trip_id=trip_id,
            image_refs=event.image_refs,
            raw_payload=event.raw_payload,
            links=EntityLinks(
                self=link_event(event.id),
                vehicle=link_vehicle(event.vehicle_profile_id),
                trip=link_trip(trip_id) if trip_id else None,
            ),
        )

    def list_trips(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        status: TripStatus | None,
        plate: str | None,
        camera_id: str | None,
        time_range: TimeRange,
    ) -> PaginatedResponse[TripSummary]:
        query = select(Trip, VehicleProfile).join(
            VehicleProfile, Trip.vehicle_profile_id == VehicleProfile.id
        )

        normalized = normalize_plate_query(plate)
        if normalized:
            query = query.where(VehicleProfile.normalized_plate.ilike(f"%{normalized}%"))
        if status is not None:
            query = query.where(Trip.status == status)
        if camera_id:
            internal_camera = db.scalar(select(Camera).where(Camera.camera_id == camera_id))
            if internal_camera is None:
                return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)
            query = query.where(
                Trip.id.in_(
                    select(TripEvent.trip_id)
                    .join(VehicleEvent, TripEvent.vehicle_event_id == VehicleEvent.id)
                    .where(VehicleEvent.camera_id == internal_camera.id)
                )
            )
        activity_at = func.coalesce(Trip.started_at, Trip.ended_at)
        query = apply_time_range(query, activity_at, time_range)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = db.execute(
            query.order_by(Trip.started_at.desc().nullslast(), Trip.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedResponse(
            items=[self._trip_summary(db, trip, profile) for trip, profile in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_trip(self, db: Session, trip_id: UUID) -> TripDetailResponse:
        try:
            detail = get_trip_with_events(db, trip_id)
        except ValueError as exc:
            raise ReadError("Trip not found", code="trip_not_found") from exc

        profile = db.get(VehicleProfile, detail.trip.vehicle_profile_id)
        if profile is None:
            raise ReadError("Vehicle profile not found", code="vehicle_not_found")

        auth_status = self._trip_authorization_status(db, detail.trip)
        events = [
            TripEventView(
                id=row.event.id,
                sequence=row.sequence,
                captured_at=row.event.captured_at,
                plate=row.event.effective_plate or row.event.normalized_plate,
                plate_status=row.event.plate_status,
                zone_type=row.camera.zone_type,
                camera_id=row.camera.camera_id,
                camera_label=row.camera.label,
                image_refs=row.event.image_refs,
                links=EntityLinks(
                    self=link_event(row.event.id),
                    vehicle=link_vehicle(row.event.vehicle_profile_id),
                    trip=link_trip(trip_id),
                ),
            )
            for row in detail.events
        ]

        return TripDetailResponse(
            id=detail.trip.id,
            status=detail.trip.status,
            started_at=detail.trip.started_at,
            ended_at=detail.trip.ended_at,
            vehicle_profile=self._vehicle_brief(profile),
            authorization_status=auth_status,
            events=events,
            links=EntityLinks(
                self=link_trip(detail.trip.id),
                vehicle=link_vehicle(profile.id),
            ),
        )

    def get_roster(self, db: Session) -> list[RosterItem]:
        return [
            RosterItem(
                vehicle_profile_id=entry.vehicle_profile_id,
                plate=entry.normalized_plate,
                entry_time=entry.entry_time,
                authorization_status=entry.authorization_status,
                trip_id=entry.trip_id,
                links=EntityLinks(
                    self=link_trip(entry.trip_id),
                    vehicle=link_vehicle(entry.vehicle_profile_id),
                    trip=link_trip(entry.trip_id),
                ),
            )
            for entry in get_active_roster(db)
        ]

    def report_entries(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        plate: str | None,
        time_range: TimeRange,
    ) -> PaginatedResponse[ReportEventRow]:
        return self._zone_report(
            db,
            zone_type=ZoneType.ENTRY,
            page=page,
            page_size=page_size,
            plate=plate,
            time_range=time_range,
        )

    def report_exits(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        plate: str | None,
        time_range: TimeRange,
    ) -> PaginatedResponse[ReportEventRow]:
        return self._zone_report(
            db,
            zone_type=ZoneType.EXIT,
            page=page,
            page_size=page_size,
            plate=plate,
            time_range=time_range,
        )

    def report_transits(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        camera_ids: list[str],
        plate: str | None,
        time_range: TimeRange,
    ) -> PaginatedResponse[ReportEventRow]:
        if not camera_ids:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)

        cameras = db.scalars(select(Camera).where(Camera.camera_id.in_(camera_ids))).all()
        if not cameras:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)

        query = (
            select(VehicleEvent, Camera)
            .join(Camera, VehicleEvent.camera_id == Camera.id)
            .where(VehicleEvent.camera_id.in_([camera.id for camera in cameras]))
        )
        normalized = normalize_plate_query(plate)
        if normalized:
            query = query.where(VehicleEvent.normalized_plate.ilike(f"%{normalized}%"))
        query = apply_time_range(query, VehicleEvent.captured_at, time_range)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = db.execute(
            query.order_by(VehicleEvent.captured_at.desc(), VehicleEvent.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedResponse(
            items=[self._report_row(db, event, camera) for event, camera in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def report_trips(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        status: TripStatus | None,
        plate: str | None,
        time_range: TimeRange,
    ) -> PaginatedResponse[TripSummary]:
        return self.list_trips(
            db,
            page=page,
            page_size=page_size,
            status=status,
            plate=plate,
            camera_id=None,
            time_range=time_range,
        )

    def _zone_report(
        self,
        db: Session,
        *,
        zone_type: ZoneType,
        page: int,
        page_size: int,
        plate: str | None,
        time_range: TimeRange,
    ) -> PaginatedResponse[ReportEventRow]:
        query = (
            select(VehicleEvent, Camera)
            .join(Camera, VehicleEvent.camera_id == Camera.id)
            .where(Camera.zone_type == zone_type)
        )
        normalized = normalize_plate_query(plate)
        if normalized:
            query = query.where(VehicleEvent.normalized_plate.ilike(f"%{normalized}%"))
        query = apply_time_range(query, VehicleEvent.captured_at, time_range)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = db.execute(
            query.order_by(VehicleEvent.captured_at.desc(), VehicleEvent.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedResponse(
            items=[self._report_row(db, event, camera) for event, camera in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _vehicle_brief(self, profile: VehicleProfile) -> VehicleProfileBrief:
        return VehicleProfileBrief(id=profile.id, plate=profile.normalized_plate)

    def _vehicle_search_item(self, profile: VehicleProfile) -> VehicleSearchItem:
        return VehicleSearchItem(
            id=profile.id,
            plate=profile.normalized_plate,
            normalized_plate=profile.normalized_plate,
            last_seen_at=profile.last_seen_at,
            links=EntityLinks(self=link_vehicle(profile.id)),
        )

    def _event_summary(self, event: VehicleEvent, camera: Camera) -> EventSummary:
        trip_id = None  # avoid extra query in list views
        return EventSummary(
            id=event.id,
            captured_at=event.captured_at,
            plate=event.raw_plate,
            effective_plate=event.effective_plate,
            plate_status=event.plate_status,
            authorization_status=event.authorization_status,
            camera_id=camera.camera_id,
            camera_label=camera.label,
            zone_type=camera.zone_type,
            links=EntityLinks(
                self=link_event(event.id),
                vehicle=link_vehicle(event.vehicle_profile_id),
                trip=link_trip(trip_id) if trip_id else None,
            ),
        )

    def _trip_summary(
        self,
        db: Session,
        trip: Trip,
        profile: VehicleProfile,
    ) -> TripSummary:
        event_count = db.scalar(
            select(func.count()).where(TripEvent.trip_id == trip.id)
        ) or 0
        return TripSummary(
            id=trip.id,
            status=trip.status,
            started_at=trip.started_at,
            ended_at=trip.ended_at,
            vehicle_profile=self._vehicle_brief(profile),
            authorization_status=self._trip_authorization_status(db, trip),
            event_count=event_count,
            links=EntityLinks(
                self=link_trip(trip.id),
                vehicle=link_vehicle(profile.id),
            ),
        )

    def _trip_authorization_status(
        self,
        db: Session,
        trip: Trip,
    ) -> AuthorizationStatus | None:
        if trip.entry_event_id is None:
            return None
        entry = db.get(VehicleEvent, trip.entry_event_id)
        return entry.authorization_status if entry else None

    def _report_row(
        self,
        db: Session,
        event: VehicleEvent,
        camera: Camera,
    ) -> ReportEventRow:
        trip_id = db.scalar(
            select(TripEvent.trip_id).where(TripEvent.vehicle_event_id == event.id)
        )
        trip_status = None
        if trip_id:
            trip = db.get(Trip, trip_id)
            trip_status = trip.status if trip else None

        return ReportEventRow(
            plate=event.effective_plate or event.normalized_plate,
            event_time=event.captured_at,
            camera_label=camera.label,
            authorization_status=event.authorization_status,
            trip_id=trip_id,
            trip_status=trip_status,
            links=EntityLinks(
                self=link_event(event.id),
                vehicle=link_vehicle(event.vehicle_profile_id),
                trip=link_trip(trip_id) if trip_id else None,
            ),
        )
