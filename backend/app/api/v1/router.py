"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import config, health

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(config.router, tags=["config"])
