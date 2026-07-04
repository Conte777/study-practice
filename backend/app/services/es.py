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

from elasticsearch import Elasticsearch, helpers

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
        "file_name": {"type": "keyword"},
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


@lru_cache(maxsize=1)
def get_client() -> Elasticsearch:
    """Return a process-wide Elasticsearch client built from settings."""
    return Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=10)


def ensure_index() -> None:
    """Create the ``documents`` index with the Russian analyzer if absent."""
    client = get_client()
    if not client.indices.exists(index=INDEX):
        client.indices.create(index=INDEX, settings=_INDEX_SETTINGS, mappings=_INDEX_MAPPINGS)
        logger.info("Created Elasticsearch index %r", INDEX)


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


def search_chunks(q: str, from_: int, size: int) -> tuple[int, list[dict]]:
    """Run a full-text search over indexed chunks.

    Args:
        q: User query string.
        from_: Pagination offset.
        size: Page size.

    Returns:
        A ``(total, hits)`` tuple where ``hits`` are raw Elasticsearch hit
        dicts (each with ``_source``, ``_score`` and optional ``highlight``).
    """
    response = get_client().search(
        index=INDEX,
        from_=from_,
        size=size,
        query={"multi_match": {"query": q, "fields": ["text"]}},
        highlight={"fields": {"text": {"pre_tags": ["<mark>"], "post_tags": ["</mark>"]}}},
    )
    total = response["hits"]["total"]["value"]
    return total, response["hits"]["hits"]
