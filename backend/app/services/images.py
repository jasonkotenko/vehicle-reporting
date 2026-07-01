"""Image fetch background hook."""

from __future__ import annotations

import logging
from uuid import UUID

from app.services.image_fetch import ImageFetchService

logger = logging.getLogger(__name__)


def enqueue_image_fetch(event_id: UUID, image_urls: list[str]) -> None:
    """Fetch and store CV images after ingest commits."""
    del image_urls  # refs are read from the persisted event
    try:
        ImageFetchService().fetch_event_images(event_id)
    except Exception:
        logger.exception("Background image fetch failed for event %s", event_id)
