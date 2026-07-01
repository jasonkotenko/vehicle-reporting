"""Image storage configuration helpers."""

from __future__ import annotations

import mimetypes
from pathlib import PurePosixPath


def extension_for_content_type(content_type: str) -> str:
    normalized = content_type.split(";", 1)[0].strip().lower()
    extension = mimetypes.guess_extension(normalized) or ".jpg"
    if extension == ".jpe":
        extension = ".jpg"
    return extension


def validate_image_key(key: str) -> None:
    if not key:
        raise ValueError("Image key is required")
    if ".." in key or key.startswith("/") or "\\" in key:
        raise ValueError("Invalid image key")
    path = PurePosixPath(key)
    if len(path.parts) != 2:
        raise ValueError("Invalid image key layout")
    for part in path.parts:
        if not part or part in {".", ".."}:
            raise ValueError("Invalid image key segment")
