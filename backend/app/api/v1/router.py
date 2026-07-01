"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import auth, config, health, ingest
from app.api.v1.admin.router import router as admin_router

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(config.router, tags=["config"])
router.include_router(auth.router, tags=["auth"])
router.include_router(ingest.router, tags=["ingest"])
router.include_router(admin_router, tags=["admin"])
