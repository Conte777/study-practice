import pytest

from app.services import cache
from tests.conftest import es_available, make_docx, redis_available

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _require_services():
    if not (es_available() and redis_available()):
        pytest.skip("Elasticsearch/Redis not reachable")


def test_second_query_served_from_cache(client, monkeypatch):
    term = "кэшированныйтермин"
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("c.docx", make_docx(f"текст со словом {term}"), "")},
    )
    client.get("/api/v1/search", params={"q": term})  # populates cache

    import app.api.search as search_mod

    calls = {"n": 0}
    real = search_mod.search_chunks

    def spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(search_mod, "search_chunks", spy)
    client.get("/api/v1/search", params={"q": term})
    assert calls["n"] == 0  # cache hit, ES not touched


def test_key_normalization_and_ttl():
    cache.set_cached("Hello   World", 0, 10, {"total": 0, "results": []})
    assert cache.get_cached("hello world", 0, 10) is not None  # case/space insensitive
    ttl = cache.get_client().ttl(cache._key("hello world", 0, 10))
    assert 0 < ttl <= cache.TTL_SECONDS


def test_redis_down_degrades_gracefully(monkeypatch):
    cache.get_client.cache_clear()
    monkeypatch.setattr(cache.settings, "REDIS_URL", "redis://localhost:6390/0")
    try:
        assert cache.get_cached("anything", 0, 10) is None  # no raise
        cache.set_cached("anything", 0, 10, {"total": 0, "results": []})  # no raise
    finally:
        cache.get_client.cache_clear()
