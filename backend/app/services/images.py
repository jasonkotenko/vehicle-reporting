"""Image fetch enqueue stub — implemented in step 11."""

from __future__ import annotations

import logging
from uuid import UUID

logger = logging.getLogger(__name__)


def enqueue_image_fetch(event_id: UUID, image_urls: list[str]) -> None:
    """Background hook for step 11 to fetch and store CV images."""
    logger.info(
        "Image fetch queued for event %s (%d url(s)); step 11 not implemented yet",
        event_id,
        len(image_urls),
    )
