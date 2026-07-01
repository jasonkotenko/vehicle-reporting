"""Stored image serving routes."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.core.images import validate_image_key
from app.services.image_storage import get_image_storage
from app.services.image_tokens import ImageTokenError, verify_image_access_token

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/{image_key:path}")
def serve_image(image_key: str, token: str = Query(...)) -> Response:
    try:
        validate_image_key(image_key)
        verify_image_access_token(token, image_key)
    except (ValueError, ImageTokenError) as exc:
        raise HTTPException(status_code=403, detail="Invalid image access") from exc

    storage = get_image_storage()
    try:
        content, content_type = storage.read(image_key)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail="Image not found") from None

    return Response(content=content, media_type=content_type)
