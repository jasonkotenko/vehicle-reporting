"""Admin API routes."""

from fastapi import APIRouter

from app.api.v1.admin import authorized_vehicles, cameras

router = APIRouter(prefix="/admin")
router.include_router(cameras.router)
router.include_router(authorized_vehicles.router)
