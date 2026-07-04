"""Real auth flow via `raw_client` (no dependency override)."""

from unittest.mock import patch

import pytest

CREDS = {"username": "alice", "password": "secretpw1"}


def _register(raw_client, creds=CREDS):
    return raw_client.post("/api/v1/auth/register", json=creds)


def test_register_returns_token(raw_client):
    r = _register(raw_client)
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_duplicate_register_409(raw_client):
    assert _register(raw_client).status_code == 200
    assert _register(raw_client).status_code == 409


def test_login_then_access_protected(raw_client):
    _register(raw_client)
    tok = raw_client.post("/api/v1/auth/login", json=CREDS).json()["access_token"]
    with (
        patch("app.api.search.search_chunks", return_value=(0, [])),
        patch("app.services.cache.get_cached", return_value=None),
        patch("app.services.cache.set_cached"),
    ):
        r = raw_client.get(
            "/api/v1/search",
            params={"q": "x"},
            headers={"Authorization": f"Bearer {tok}"},
        )
    assert r.status_code == 200


def test_wrong_password_401(raw_client):
    _register(raw_client)
    r = raw_client.post("/api/v1/auth/login", json={"username": "alice", "password": "wrongpass1"})
    assert r.status_code == 401


def test_unknown_user_401(raw_client):
    r = raw_client.post("/api/v1/auth/login", json={"username": "ghost", "password": "whatever12"})
    assert r.status_code == 401


def test_no_token_rejected(raw_client):
    assert raw_client.get("/api/v1/search", params={"q": "x"}).status_code in (401, 403)


def test_history_requires_auth(raw_client):
    assert raw_client.get("/api/v1/search/history").status_code in (401, 403)


def test_bad_token_401(raw_client):
    r = raw_client.get(
        "/api/v1/search", params={"q": "x"}, headers={"Authorization": "Bearer garbage"}
    )
    assert r.status_code == 401


@pytest.mark.parametrize("field", ["username", "password"])
def test_missing_field_422(raw_client, field):
    body = {k: v for k, v in CREDS.items() if k != field}
    assert raw_client.post("/api/v1/auth/register", json=body).status_code == 422


def test_health_open(raw_client):
    assert raw_client.get("/api/v1/health").status_code == 200
