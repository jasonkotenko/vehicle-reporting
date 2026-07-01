"""Trip computation stub — implemented in step 6."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def recompute_trips_for_profile(db: Session, vehicle_profile_id: UUID) -> None:
    """Recompute trips for a vehicle profile after a new event is ingested."""
    logger.debug(
        "Trip recompute queued for profile %s; step 6 not implemented yet",
        vehicle_profile_id,
    )
    db.flush()
