"""Smoke checks that the endpoints honor the wire contract (schemas + statuses)."""

import io
import os

import pytest

from tests.conftest import es_available, make_docx


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_upload_rejects_wrong_type(client):
    r = client.post(
        "/api/v1/documents/upload",
        files={"file": ("note.txt", b"hi", "text/plain")},
    )
    assert r.status_code == 400
    assert "detail" in r.json()


def test_upload_ok(client):
    pdf = ("ok.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")
    r = client.post("/api/v1/documents/upload", files={"file": pdf})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "uploaded"
    assert set(body) == {"id", "file_name", "status", "uploaded_at"}


def test_search_ok(client):
    if not es_available():
        pytest.skip("Elasticsearch not reachable")
    term = "капибара"
    up = client.post(
        "/api/v1/documents/upload",
        files={"file": ("k.docx", make_docx(f"Уникальное слово {term} в тексте"), "")},
    )
    assert up.status_code == 200
    r = client.get("/api/v1/search", params={"q": term})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    first = body["results"][0]
    assert set(first) == {"chunk_id", "file_name", "page", "text", "score", "highlight"}
    assert "<mark>" in (first["highlight"] or "")


def test_search_empty_q(client):
    assert client.get("/api/v1/search", params={"q": ""}).status_code == 400


def test_unknown_route_404_with_detail_body(client):
    r = client.get("/api/v1/nope")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_invalid_pagination_returns_422_with_string_detail(client):
    r = client.get("/api/v1/search", params={"q": "x", "size": 0})
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], str)


def test_upload_db_failure_cleans_up_temp_file(monkeypatch):
    from fastapi.testclient import TestClient

    import app.api.documents as documents_mod
    from app.main import app

    captured = {}
    real_unlink = documents_mod.unlink

    def spy_unlink(path):
        captured["path"] = path
        real_unlink(path)

    def failing_commit(_self):
        raise RuntimeError("db down")

    monkeypatch.setattr(documents_mod, "unlink", spy_unlink)
    monkeypatch.setattr("sqlalchemy.orm.Session.commit", failing_commit)

    no_raise_client = TestClient(app, raise_server_exceptions=False)
    pdf = ("ok.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")
    r = no_raise_client.post("/api/v1/documents/upload", files={"file": pdf})

    assert r.status_code == 500
    assert "path" in captured
    assert not os.path.exists(captured["path"])


def test_unhandled_error_returns_500_with_detail_body(monkeypatch):
    from fastapi.testclient import TestClient

    import app.api.search as search_mod
    from app.main import app

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(search_mod, "search_chunks", boom)
    monkeypatch.setattr(search_mod.cache, "get_cached", lambda *a, **k: None)
    # raise_server_exceptions=False: exercise the registered 500 handler
    # instead of TestClient's default behavior of re-raising for debugging.
    no_raise_client = TestClient(app, raise_server_exceptions=False)
    r = no_raise_client.get("/api/v1/search", params={"q": "x"})
    assert r.status_code == 500
    assert r.json() == {"detail": "Internal server error"}
