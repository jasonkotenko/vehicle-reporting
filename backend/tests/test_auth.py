"""Authentication endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_returns_token_for_admin() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "ADMIN"
    assert body["user"]["active"] is True


def test_login_rejects_invalid_password() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_requires_authentication() -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(admin_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/auth/me", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert response.json()["active"] is True
