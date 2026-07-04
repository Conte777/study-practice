"""Background ingestion pipeline: parse → chunk → index.

Runs after the upload response is returned, so the client is never blocked on
Elasticsearch. The document row's ``status`` tracks progress
(uploaded → indexing → indexed), and any failure downgrades it to ``error``
without propagating — a broken document must not take down the worker.
"""

import logging
import uuid

from app.core.db import SessionLocal
from app.models import Document, DocumentStatus
from app.services.chunker import chunk_text
from app.services.es import Chunk, index_document
from app.services.parser import extract_text
from app.services.uploads import unlink

logger = logging.getLogger(__name__)


def process_document(document_id: str, file_name: str, path: str, file_type: str) -> None:
    """Parse, chunk, and index an uploaded file, updating its DB status.

    Args:
        document_id: Document UUID (string form).
        file_name: Original file name.
        path: Temp path of the saved upload; deleted when processing finishes.
        file_type: ``"pdf"`` or ``"docx"``.
    """
    db = SessionLocal()
    try:
        pages = extract_text(path, file_type)
        chunks = [
            Chunk(page_number=page.page_number, text=text)
            for page in pages
            for text in chunk_text(page.text)
        ]
        _set_status(db, document_id, DocumentStatus.indexing)
        index_document(document_id, file_name, chunks)
        _set_status(db, document_id, DocumentStatus.indexed)
    except Exception:  # noqa: BLE001 — indexing failure must not crash the worker
        logger.exception("Indexing failed for document %s", document_id)
        _set_status(db, document_id, DocumentStatus.error)
    finally:
        db.close()
        unlink(path)


def _set_status(db, document_id: str, status: DocumentStatus) -> None:
    doc = db.get(Document, uuid.UUID(document_id))
    if doc is not None:
        doc.status = status
        db.commit()
