"""CV/ALPR ingest endpoint."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import verify_ingest_api_key
from app.db.session import get_db
from app.schemas.ingest import IngestEventRequest, IngestEventResponse
from app.services.images import enqueue_image_fetch
from app.services.ingest import IngestService

router = APIRouter(prefix="/ingest")


@router.post(
    "/events",
    response_model=IngestEventResponse,
    responses={
        status.HTTP_200_OK: {"model": IngestEventResponse},
        status.HTTP_201_CREATED: {"model": IngestEventResponse},
    },
)
async def ingest_event(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(verify_ingest_api_key),
) -> JSONResponse:
    raw_payload = await request.json()
    payload = IngestEventRequest.model_validate(raw_payload)
    result = IngestService().process_event(db, payload, raw_payload=raw_payload)

    if not result.is_duplicate:
        background_tasks.add_task(
            enqueue_image_fetch,
            result.event_id,
            payload.image_urls,
        )

    response = IngestEventResponse(
        event_id=result.event_id,
        vehicle_profile_id=result.vehicle_profile_id,
    )
    status_code = status.HTTP_200_OK if result.is_duplicate else status.HTTP_201_CREATED
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
    )
