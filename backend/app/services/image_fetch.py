"""Fetch CV images at ingest and persist to storage."""

from __future__ import annotations

import logging
from copy import deepcopy
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import VehicleEvent
from app.services.image_storage import get_image_storage

logger = logging.getLogger(__name__)


class ImageFetchService:
    def fetch_event_images(self, event_id: UUID) -> None:
        db = SessionLocal()
        try:
            event = db.get(VehicleEvent, event_id)
            if event is None:
                logger.warning("Image fetch skipped; event not found: %s", event_id)
                return

            updated_refs = deepcopy(event.image_refs)
            changed = False
            storage = get_image_storage()
            settings = get_settings()

            with httpx.Client(timeout=settings.image_fetch_timeout_seconds) as client:
                for ref in updated_refs:
                    if ref.get("status") != "pending":
                        continue

                    source_url = ref.get("source_url")
                    if not source_url:
                        ref["status"] = "fetch_failed"
                        ref["error"] = "missing source_url"
                        changed = True
                        continue

                    if not self._is_url_allowed(source_url):
                        ref["status"] = "fetch_failed"
                        ref["error"] = "url_not_allowed"
                        changed = True
                        continue

                    try:
                        data, content_type = self._download_image(client, source_url)
                        key = storage.store(data, content_type)
                        ref["status"] = "stored"
                        ref["key"] = key
                        ref["content_type"] = content_type
                        ref.pop("error", None)
                        changed = True
                    except Exception as exc:  # noqa: BLE001 - persist failure per ref
                        logger.warning(
                            "Image fetch failed for event %s url %s: %s",
                            event_id,
                            source_url,
                            exc,
                        )
                        ref["status"] = "fetch_failed"
                        ref["error"] = str(exc)
                        changed = True

            if changed:
                event.image_refs = updated_refs
                db.commit()
        finally:
            db.close()

    def _is_url_allowed(self, url: str) -> bool:
        if not url.startswith(("http://", "https://")):
            return False

        prefixes = get_settings().cv_image_url_allowlist_prefixes
        if not prefixes:
            return True
        return any(url.startswith(prefix) for prefix in prefixes)

    def _download_image(self, client: httpx.Client, url: str) -> tuple[bytes, str]:
        settings = get_settings()
        with client.stream("GET", url) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "image/jpeg").split(";", 1)[0]
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > settings.image_max_bytes:
                    raise ValueError("image exceeds max size")
                chunks.append(chunk)
            return b"".join(chunks), content_type
