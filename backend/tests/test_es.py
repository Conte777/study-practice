import uuid

import pytest

from app.services import es
from tests.conftest import es_available

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _require_es():
    if not es_available():
        pytest.skip("Elasticsearch not reachable")


def _count(doc_id: str) -> int:
    return es.get_client().count(index=es.INDEX, query={"term": {"document_id": doc_id}})["count"]


def test_index_count_matches_chunks():
    es.ensure_index()
    doc_id = str(uuid.uuid4())
    chunks = [es.Chunk(1, "Привет мир"), es.Chunk(1, "второй кусок текста")]
    assert es.index_document(doc_id, "t.docx", chunks) == 2
    assert _count(doc_id) == 2


def test_reindex_is_idempotent():
    es.ensure_index()
    doc_id = str(uuid.uuid4())
    chunks = [es.Chunk(1, "одинаковый текст"), es.Chunk(2, "ещё текст")]
    es.index_document(doc_id, "t.docx", chunks)
    es.index_document(doc_id, "t.docx", chunks)  # same deterministic _id -> overwrite
    assert _count(doc_id) == 2


def test_ensure_index_tolerates_concurrent_create_race():
    es.ensure_index()  # index already exists at this point

    # Simulate a second caller losing the exists-check race: exists() lies
    # (says "no") so create() runs against an index that's already there.
    client = es.get_client()
    original_exists = client.indices.exists
    client.indices.exists = lambda **k: False
    try:
        es.ensure_index()  # must not raise
    finally:
        client.indices.exists = original_exists


def test_mapping_has_russian_analyzer():
    es.ensure_index()
    client = es.get_client()
    props = client.indices.get_mapping(index=es.INDEX)[es.INDEX]["mappings"]["properties"]
    assert props["text"]["analyzer"] == "ru"
    analysis = client.indices.get_settings(index=es.INDEX)[es.INDEX]["settings"]["index"][
        "analysis"
    ]
    assert analysis["analyzer"]["ru"]["type"] == "russian"
