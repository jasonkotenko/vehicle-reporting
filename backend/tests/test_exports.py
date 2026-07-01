"""Export API integration tests."""

from __future__ import annotations

import csv
import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


@pytest.fixture
def ingest_headers() -> dict[str, str]:
    return {"X-Ingest-Key": get_settings().ingest_api_key}


def _ingest_entry(ingest_headers: dict[str, str], plate: str) -> None:
    response = client.post(
        "/api/v1/ingest/events",
        headers=ingest_headers,
        json={
            "external_id": f"export-{uuid.uuid4()}",
            "camera_id": "CAM-MAIN-ENTRY",
            "timestamp": "2026-07-04T09:00:00+08:00",
            "license_plate": plate,
            "plate_status": "READ",
            "image_urls": ["http://cv-host/snapshots/a.jpg"],
        },
    )
    assert response.status_code == 201


def test_entries_csv_row_count_matches_json_total(
    admin_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"CSV{uuid.uuid4().hex[:6].upper()}"
    _ingest_entry(ingest_headers, plate)

    params = {
        "from": "2026-07-04T00:00:00+08:00",
        "to": "2026-07-04T23:59:59+08:00",
        "plate": plate,
    }
    json_response = client.get("/api/v1/reports/entries", headers=admin_headers, params=params)
    csv_response = client.get(
        "/api/v1/reports/entries",
        headers=admin_headers,
        params={**params, "format": "csv"},
    )

    assert json_response.status_code == 200
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "attachment" in csv_response.headers["content-disposition"]
    assert csv_response.headers["content-disposition"].endswith('.csv"')

    total = json_response.json()["total"]
    content = csv_response.text.lstrip("\ufeff")
    rows = list(csv.reader(io.StringIO(content)))
    assert rows[0] == [
        "plate",
        "entry_time",
        "camera_label",
        "authorization_status",
        "trip_id",
        "trip_status",
    ]
    assert len(rows) - 1 == total


def test_entries_pdf_returns_valid_content_type(
    admin_headers: dict[str, str],
    ingest_headers: dict[str, str],
) -> None:
    plate = f"PDF{uuid.uuid4().hex[:6].upper()}"
    _ingest_entry(ingest_headers, plate)

    response = client.get(
        "/api/v1/reports/entries",
        headers=admin_headers,
        params={
            "from": "2026-07-04T00:00:00+08:00",
            "to": "2026-07-04T23:59:59+08:00",
            "plate": plate,
            "format": "pdf",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "attachment" in response.headers["content-disposition"]


def test_roster_csv_export(operator_headers: dict[str, str]) -> None:
    response = client.get(
        "/api/v1/roster",
        headers=operator_headers,
        params={"format": "csv"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.text.lstrip("\ufeff")
    rows = list(csv.reader(io.StringIO(content)))
    assert rows[0][0] == "plate"


def test_invalid_export_format_returns_400(admin_headers: dict[str, str]) -> None:
    response = client.get(
        "/api/v1/reports/entries",
        headers=admin_headers,
        params={"format": "xlsx"},
    )
    assert response.status_code == 400
