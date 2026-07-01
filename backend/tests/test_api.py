from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.plates import normalize_plate
from app.core.timezone import parse_display_datetime, to_display
from app.main import app

client = TestClient(app)


def test_root_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_v1_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_v1_config() -> None:
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    body = response.json()
    assert body["display_timezone"] == "Asia/Manila"


def test_openapi_docs_available() -> None:
    response = client.get("/docs")
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("abc 1234", "ABC1234"),
        ("ab-cd 12", "ABCD12"),
        (None, None),
        ("", None),
        ("---", None),
    ],
)
def test_normalize_plate(raw: str | None, expected: str | None) -> None:
    assert normalize_plate(raw) == expected


def test_to_display_converts_utc_to_manila() -> None:
    utc_time = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
    manila_time = to_display(utc_time, "Asia/Manila")
    assert manila_time.hour == 8


def test_parse_display_datetime_interprets_naive_as_display_tz() -> None:
    parsed = parse_display_datetime("2026-07-01T08:00:00", "Asia/Manila")
    assert parsed == datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
