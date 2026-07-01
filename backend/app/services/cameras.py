"""Camera registration and management."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Camera
from app.schemas.camera import CameraCreate, CameraUpdate
from app.services.admin_errors import AdminError


class CameraService:
    def list_cameras(self, db: Session) -> list[Camera]:
        return list(db.scalars(select(Camera).order_by(Camera.camera_id)))

    def get_camera(self, db: Session, camera_id: UUID) -> Camera:
        camera = db.get(Camera, camera_id)
        if camera is None:
            raise AdminError("Camera not found", code="camera_not_found", status_code=404)
        return camera

    def create_camera(self, db: Session, payload: CameraCreate) -> Camera:
        existing = db.scalar(select(Camera).where(Camera.camera_id == payload.camera_id))
        if existing is not None:
            raise AdminError(
                f"Camera ID already exists: {payload.camera_id}",
                code="duplicate_camera_id",
                status_code=409,
            )

        camera = Camera(
            camera_id=payload.camera_id,
            label=payload.label,
            zone_type=payload.zone_type,
        )
        db.add(camera)
        db.commit()
        db.refresh(camera)
        return camera

    def update_camera(self, db: Session, camera_id: UUID, payload: CameraUpdate) -> Camera:
        camera = self.get_camera(db, camera_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return camera

        for field, value in updates.items():
            setattr(camera, field, value)

        db.commit()
        db.refresh(camera)
        return camera

    def deactivate_camera(self, db: Session, camera_id: UUID) -> Camera:
        camera = self.get_camera(db, camera_id)
        camera.active = False
        db.commit()
        db.refresh(camera)
        return camera
