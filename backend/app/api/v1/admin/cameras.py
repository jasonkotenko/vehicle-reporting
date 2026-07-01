"""Admin camera management routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.db.session import get_db
from app.schemas.camera import CameraCreate, CameraResponse, CameraUpdate
from app.services.cameras import CameraService

router = APIRouter(prefix="/cameras", tags=["admin-cameras"])


@router.get("", response_model=list[CameraResponse])
def list_cameras(
    _: AdminUser,
    db: Session = Depends(get_db),
) -> list[CameraResponse]:
    return CameraService().list_cameras(db)


@router.post("", response_model=CameraResponse, status_code=201)
def create_camera(
    payload: CameraCreate,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> CameraResponse:
    return CameraService().create_camera(db, payload)


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(
    camera_id: UUID,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> CameraResponse:
    return CameraService().get_camera(db, camera_id)


@router.patch("/{camera_id}", response_model=CameraResponse)
def update_camera(
    camera_id: UUID,
    payload: CameraUpdate,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> CameraResponse:
    return CameraService().update_camera(db, camera_id, payload)


@router.delete("/{camera_id}", response_model=CameraResponse)
def deactivate_camera(
    camera_id: UUID,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> CameraResponse:
    return CameraService().deactivate_camera(db, camera_id)
