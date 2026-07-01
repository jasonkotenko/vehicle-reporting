import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("INGEST_API_KEY", "test-ingest-key")
os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get("DATABASE_URL", "postgresql+psycopg://vvt:change-me@db:5432/vvt"),
)
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("IMAGE_FETCH_TIMEOUT_SECONDS", "1")
os.environ.setdefault("PUBLIC_API_URL", "http://testserver")

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models import User
from app.models.enums import UserRole

client = TestClient(app)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def operator_headers() -> dict[str, str]:
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.username == "operator"))
        if existing is None:
            db.add(
                User(
                    username="operator",
                    password_hash=hash_password("operator"),
                    display_name="Test Operator",
                    role=UserRole.OPERATOR,
                )
            )
            db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "operator", "password": "operator"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def disable_background_image_fetch(request, monkeypatch):
    """Avoid slow HTTP fetches to cv-host during unrelated ingest tests."""
    if request.module.__name__ == "tests.test_images":
        return

    def noop(_event_id, _image_urls) -> None:
        return None

    monkeypatch.setattr("app.api.v1.ingest.enqueue_image_fetch", noop)
