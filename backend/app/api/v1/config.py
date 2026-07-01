"""Public configuration for clients."""

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.config import AppConfigResponse

router = APIRouter()


@router.get("/config", response_model=AppConfigResponse)
def get_app_config(settings: Settings = Depends(get_settings)) -> AppConfigResponse:
    return AppConfigResponse(display_timezone=settings.display_timezone)
