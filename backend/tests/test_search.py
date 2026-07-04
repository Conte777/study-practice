"""QA-01 — /search and /documents contract + validation."""

import pytest

SEARCH_KEYS = {"chunk_id", "file_name", "page", "text", "score", "highlight"}


def test_search_returns_results_and_total(client):
    r = client.get("/api/v1/search", params={"q": "elasticsearch"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["results"])
    assert body["results"], "expected non-empty mock results"
    for item in body["results"]:
        assert set(item) == SEARCH_KEYS
        assert isinstance(item["score"], int | float)
        assert isinstance(item["page"], int)


def test_search_highlight_wraps_query(client):
    q = "relevance"
    body = client.get("/api/v1/search", params={"q": q}).json()
    first = body["results"][0]
    assert f"<mark>{q}</mark>" in first["highlight"]
    # Contract: highlight is the same fragment as text, only marked up.
    assert q in first["text"]


@pytest.mark.parametrize("q", ["", "   ", "\t\n"])
def test_search_rejects_blank_query(client, q):
    r = client.get("/api/v1/search", params={"q": q})
    assert r.status_code == 400
    assert "detail" in r.json()


def test_search_requires_q(client):
    # Missing required query param → 422, not 500.
    assert client.get("/api/v1/search").status_code == 422


@pytest.mark.parametrize(
    ("params", "code"),
    [
        ({"q": "x", "from": -1}, 422),  # from must be >= 0
        ({"q": "x", "size": 0}, 422),  # size must be >= 1
        ({"q": "x", "size": 101}, 422),  # size must be <= 100
        ({"q": "x", "from": 0, "size": 10}, 200),
    ],
)
def test_search_pagination_bounds(client, params, code):
    assert client.get("/api/v1/search", params=params).status_code == code


def test_list_documents_shape(client):
    r = client.get("/api/v1/documents")
    assert r.status_code == 200
    docs = r.json()
    assert isinstance(docs, list) and docs
    valid_statuses = {"uploaded", "indexing", "indexed", "error"}
    for d in docs:
        assert set(d) == {"id", "file_name", "status", "uploaded_at"}
        assert d["status"] in valid_statuses
