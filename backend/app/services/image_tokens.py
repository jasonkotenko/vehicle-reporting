"""Signed URL tokens for stored images."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import quote

import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.core.images import validate_image_key
from app.core.security import ALGORITHM


class ImageTokenError(ValueError):
    pass


def create_image_access_token(image_key: str) -> str:
    validate_image_key(image_key)
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.image_signed_url_expire_minutes)
    payload = {"image_key": image_key, "exp": expire, "typ": "image"}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_image_access_token(token: str, image_key: str) -> None:
    validate_image_key(image_key)
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except InvalidTokenError as exc:
        raise ImageTokenError("Invalid image token") from exc

    if payload.get("typ") != "image" or payload.get("image_key") != image_key:
        raise ImageTokenError("Invalid image token")


def build_signed_image_url(image_key: str) -> str:
    token = create_image_access_token(image_key)
    settings = get_settings()
    base = settings.public_api_url.rstrip("/")
    encoded_key = quote(image_key, safe="/")
    return f"{base}/api/v1/images/{encoded_key}?token={token}"


def enrich_image_refs(image_refs: list) -> list[dict]:
    enriched: list[dict] = []
    for ref in image_refs:
        item = dict(ref)
        if item.get("status") == "stored" and item.get("key"):
            item["signed_url"] = build_signed_image_url(item["key"])
        enriched.append(item)
    return enriched
