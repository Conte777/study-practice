"""Search-history recording and the read endpoint (auth bypassed via `client`)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.api.search import get_db
from app.core.db import SessionLocal
from app.main import app
from app.models import SearchQuery


@pytest.fixture
def _no_cache():
    """Force a cache miss so the endpoint always hits the recording path."""
    with (
        patch("app.services.cache.get_cached", return_value=None),
        patch("app.services.cache.set_cached"),
    ):
        yield


def _mock_es(total: int):
    return patch("app.api.search.search_chunks", return_value=(total, []))


def test_first_page_records_history(client, _no_cache):
    with _mock_es(7):
        assert client.get("/api/v1/search", params={"q": "квант"}).status_code == 200
    with SessionLocal() as db:
        rows = db.query(SearchQuery).all()
        assert len(rows) == 1
        assert rows[0].query == "квант"
        assert rows[0].results_count == 7


def test_paginated_query_does_not_record(client, _no_cache):
    with _mock_es(7):
        assert client.get("/api/v1/search", params={"q": "квант", "from": 10}).status_code == 200
    with SessionLocal() as db:
        assert db.query(SearchQuery).count() == 0


def test_history_returns_newest_first(client):
    base = datetime(2026, 1, 1, tzinfo=UTC)
    with SessionLocal() as db:
        for i, q in enumerate(["one", "two", "three"]):
            db.add(SearchQuery(query=q, results_count=i, created_at=base + timedelta(minutes=i)))
        db.commit()
    body = client.get("/api/v1/search/history", params={"limit": 2}).json()
    assert [r["query"] for r in body] == ["three", "two"]
    assert set(body[0]) == {"query", "results_count", "created_at"}


def test_empty_history_returns_list(client):
    assert client.get("/api/v1/search/history").json() == []


def test_bad_limit_422(client):
    assert client.get("/api/v1/search/history", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/search/history", params={"limit": 999}).status_code == 422


def test_db_write_error_does_not_break_search(client, _no_cache):
    """A failing commit is swallowed: the search response is still 200."""
    broken = MagicMock()
    broken.commit.side_effect = RuntimeError("db down")
    app.dependency_overrides[get_db] = lambda: broken
    try:
        with _mock_es(3):
            r = client.get("/api/v1/search", params={"q": "квант"})
        assert r.status_code == 200
        broken.rollback.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_db, None)
