"""Image storage backends."""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.core.config import get_settings
from app.core.images import extension_for_content_type, validate_image_key


class ImageStorage(Protocol):
    def store(self, data: bytes, content_type: str) -> str:
        """Persist image bytes and return the storage key."""

    def read(self, key: str) -> tuple[bytes, str]:
        """Load image bytes and content type for a stored key."""

    def exists(self, key: str) -> bool:
        """Return whether the key exists in storage."""


class LocalImageStorage:
    def __init__(self, root_path: str) -> None:
        self._root = Path(root_path)

    def store(self, data: bytes, content_type: str) -> str:
        extension = extension_for_content_type(content_type)
        key_id = uuid4().hex
        key = f"{key_id[:2]}/{key_id}{extension}"
        validate_image_key(key)
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def read(self, key: str) -> tuple[bytes, str]:
        validate_image_key(key)
        path = self._path_for_key(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        content_type, _ = mimetypes.guess_type(path.name)
        return path.read_bytes(), content_type or "application/octet-stream"

    def exists(self, key: str) -> bool:
        validate_image_key(key)
        return self._path_for_key(key).is_file()

    def _path_for_key(self, key: str) -> Path:
        validate_image_key(key)
        resolved = (self._root / key).resolve()
        root = self._root.resolve()
        if os.path.commonpath([str(resolved), str(root)]) != str(root):
            raise ValueError("Invalid image key path")
        return resolved


def get_image_storage() -> ImageStorage:
    settings = get_settings()
    if settings.image_storage_backend == "local":
        return LocalImageStorage(settings.image_storage_path)
    raise ValueError(f"Unsupported image storage backend: {settings.image_storage_backend}")
