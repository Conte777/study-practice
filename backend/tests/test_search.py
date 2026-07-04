import pytest

from tests.conftest import es_available, make_docx

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _require_es():
    if not es_available():
        pytest.skip("Elasticsearch not reachable")


def _upload(client, text: str) -> None:
    r = client.post(
        "/api/v1/documents/upload",
        files={"file": ("doc.docx", make_docx(text), "")},
    )
    assert r.status_code == 200  # background task indexes synchronously under TestClient


def test_search_returns_all_fields_scored(client):
    _upload(client, "Метеорология изучает атмосферу и погодные явления")
    body = client.get("/api/v1/search", params={"q": "метеорология атмосфера"}).json()
    assert body["total"] >= 1
    scores = [r["score"] for r in body["results"]]
    assert scores == sorted(scores, reverse=True)
    first = body["results"][0]
    assert set(first) == {"chunk_id", "file_name", "page", "text", "score", "highlight"}
    assert "<mark>" in (first["highlight"] or "")


def test_empty_query_400(client):
    assert client.get("/api/v1/search", params={"q": "   "}).status_code == 400


def test_no_match_returns_empty_200(client):
    r = client.get("/api/v1/search", params={"q": "цитробактерквазар9999"})
    assert r.status_code == 200
    assert r.json()["results"] == []
