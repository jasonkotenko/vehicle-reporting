"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers

settings = get_settings()

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="Village Vehicle Tracking API",
    version="0.1.0",
    description="API for ALPR ingest, vehicle tracking, and security reporting.",
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
def root_health() -> dict[str, str]:
    """Container orchestration health probe."""
    return {"status": "ok"}
