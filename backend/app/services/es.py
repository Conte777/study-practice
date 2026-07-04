"""Elasticsearch integration: index bootstrap, indexing, and search.

The ``documents`` index stores one Elasticsearch document per text chunk, with
a Russian analyzer on the searchable ``text`` field. Indexing is idempotent:
each chunk's ``_id`` is derived deterministically from the source document id
and chunk position, so re-indexing the same document overwrites rather than
duplicates.
"""

import logging
from dataclasses import dataclass
from functools import lru_cache

from elasticsearch import BadRequestError, Elasticsearch, helpers

from app.core.config import settings

logger = logging.getLogger(__name__)

INDEX = "documents"

# ponytail: built-in `russian` analyzer (snowball stemmer + stopwords, no plugin
# needed). Upgrade path: custom analyzer with the `analysis-morphology` plugin
# (`russian_morphology`) if lemma-accurate recall becomes a requirement.
_INDEX_SETTINGS = {
    "analysis": {
        "analyzer": {
            "ru": {
                "type": "russian",
            }
        }
    }
}
_INDEX_MAPPINGS = {
    "properties": {
        "chunk_id": {"type": "keyword"},
        "document_id": {"type": "keyword"},
        "file_name": {"type": "text", "analyzer": "ru", "fields": {"raw": {"type": "keyword"}}},
        "page_number": {"type": "integer"},
        "text": {"type": "text", "analyzer": "ru"},
    }
}


@dataclass(frozen=True)
class Chunk:
    """A text chunk ready to be indexed.

    Attributes:
        page_number: 1-based source page the chunk came from.
        text: Chunk text content.
    """

    page_number: int
    text: str


@dataclass(frozen=True)
class SearchHit:
    """A single scored search match, already translated out of ES's wire shape.

    Attributes:
        chunk_id: Deterministic ``{document_id}:{index}`` chunk identifier.
        file_name: Original file name of the source document.
        page: 1-based source page the chunk came from.
        text: Full chunk text.
        score: Elasticsearch relevance score.
        highlight: A highlighted fragment (with ``<mark>`` tags), if any.
    """

    chunk_id: str
    file_name: str
    page: int
    text: str
    score: float
    highlight: str | None


@lru_cache(maxsize=1)
def get_client() -> Elasticsearch:
    """Return a process-wide Elasticsearch client built from settings."""
    return Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=10)


def ensure_index() -> None:
    """Create the ``documents`` index with the Russian analyzer if absent.

    Tolerates the index already existing even when the preceding ``exists``
    check said otherwise: concurrent callers (background indexing jobs firing
    at the same time) can race to create it, and only one create wins.
    """
    client = get_client()
    if client.indices.exists(index=INDEX):
        return
    try:
        client.indices.create(index=INDEX, settings=_INDEX_SETTINGS, mappings=_INDEX_MAPPINGS)
        logger.info("Created Elasticsearch index %r", INDEX)
    except BadRequestError as exc:
        if exc.error != "resource_already_exists_exception":
            raise


def index_document(document_id: str, file_name: str, chunks: list[Chunk]) -> int:
    """Index a document's chunks, replacing any prior version idempotently.

    Args:
        document_id: Source document UUID (string form).
        file_name: Original file name, stored for result display.
        chunks: Ordered chunks to index.

    Returns:
        The number of chunks indexed.
    """
    ensure_index()
    actions = [
        {
            "_index": INDEX,
            "_id": f"{document_id}:{i}",
            "_source": {
                "chunk_id": f"{document_id}:{i}",
                "document_id": document_id,
                "file_name": file_name,
                "page_number": chunk.page_number,
                "text": chunk.text,
            },
        }
        for i, chunk in enumerate(chunks)
    ]
    if not actions:
        return 0
    helpers.bulk(get_client(), actions, refresh=True)
    return len(actions)


def _to_hit(raw: dict) -> SearchHit:
    src = raw["_source"]
    fragments = raw.get("highlight", {}).get("text")
    return SearchHit(
        chunk_id=src["chunk_id"],
        file_name=src["file_name"],
        page=src["page_number"],
        text=src["text"],
        score=raw["_score"],
        highlight=fragments[0] if fragments else None,
    )


def search_chunks(q: str, from_: int, size: int) -> tuple[int, list[SearchHit]]:
    """Run a full-text search over indexed chunks.

    Args:
        q: User query string.
        from_: Pagination offset.
        size: Page size.

    Returns:
        A ``(total, hits)`` tuple, translated out of Elasticsearch's wire shape.
    """
    response = get_client().search(
        index=INDEX,
        from_=from_,
        size=size,
        query={"multi_match": {"query": q, "fields": ["text", "file_name^2"]}},
        highlight={"fields": {"text": {"pre_tags": ["<mark>"], "post_tags": ["</mark>"]}}},
    )
    total = response["hits"]["total"]["value"]
    return total, [_to_hit(h) for h in response["hits"]["hits"]]
