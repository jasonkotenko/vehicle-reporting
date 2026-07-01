"""License plate normalization for matching and search."""

from __future__ import annotations


def normalize_plate(raw: str | None) -> str | None:
    """Return uppercase alphanumeric plate text for matching."""
    if not raw:
        return None
    normalized = "".join(character for character in raw.upper() if character.isalnum())
    return normalized or None
