"""Document endpoints: upload (with content/size validation) and listing."""

import os
import tempfile
import zipfile
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Document
from app.schemas import DocumentInfo, DocumentUploadResponse, ErrorResponse
from app.schemas.common import DocumentStatus
from app.services.pipeline import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_SIZE_BYTES = 20 * 1024 * 1024  # ТЗ: 20 MB limit
_READ_CHUNK = 1 << 20  # 1 MiB streaming reads


def _unlink(path: str) -> None:
    if os.path.exists(path):
        os.unlink(path)


def _sniff_type(path: str, header: bytes) -> str | None:
    """Detect the file type from content, not extension.

    Args:
        path: Path to the saved upload (needed to inspect DOCX zip entries).
        header: The first bytes of the file.

    Returns:
        ``"pdf"``, ``"docx"``, or ``None`` if the content matches neither.
    """
    if header.startswith(b"%PDF"):
        return "pdf"
    if header.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as zf:
                if any(name.startswith("word/") for name in zf.namelist()):
                    return "docx"
        except zipfile.BadZipFile:
            return None
    return None


async def _save_upload(file: UploadFile) -> tuple[str, str]:
    """Stream an upload to a temp file, enforcing the size cap and content type.

    Reads in bounded chunks so a huge upload never lands fully in memory; aborts
    as soon as the cumulative size exceeds the limit.

    Returns:
        A ``(temp_path, file_type)`` tuple.

    Raises:
        HTTPException: 400 for empty files, oversize uploads, or unsupported
            content.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115 — outlives this scope
    header = b""
    total = 0
    try:
        while chunk := await file.read(_READ_CHUNK):
            total += len(chunk)
            if total > MAX_SIZE_BYTES:
                raise HTTPException(status_code=400, detail="File exceeds 20 MB limit")
            if not header:
                header = chunk[:8]
            tmp.write(chunk)
        tmp.close()
        if total == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        file_type = _sniff_type(tmp.name, header)
        if file_type is None:
            raise HTTPException(
                status_code=400, detail="Unsupported file type (expected PDF or DOCX)"
            )
        return tmp.name, file_type
    except Exception:
        tmp.close()
        _unlink(tmp.name)
        raise


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload a document",
    description=(
        "Accept a PDF or DOCX file (validated by content, max 20 MB), persist "
        "its metadata, and return the created document."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid type or size"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> DocumentInfo:
    """Validate an uploaded document, persist its metadata, and return it.

    Parsing, chunking, and Elasticsearch indexing run in a background task so
    the response isn't blocked on them; the document's ``status`` progresses
    from ``uploaded`` to ``indexing``/``indexed`` (or ``error``) as that runs.
    """
    path, file_type = await _save_upload(file)

    doc = Document(
        id=uuid4(),
        file_name=file.filename or "unnamed",
        status=DocumentStatus.uploaded,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    background_tasks.add_task(process_document, str(doc.id), doc.file_name, path, file_type)
    return DocumentInfo(
        id=doc.id,
        file_name=doc.file_name,
        status=doc.status,
        uploaded_at=doc.uploaded_at,
    )


@router.get(
    "",
    response_model=list[DocumentInfo],
    summary="List documents",
    description="Return all uploaded documents, newest first.",
)
async def list_documents(db: Annotated[Session, Depends(get_db)]) -> list[DocumentInfo]:
    """Return all documents ordered by upload time (newest first)."""
    rows = db.scalars(select(Document).order_by(Document.uploaded_at.desc())).all()
    return [
        DocumentInfo(
            id=r.id,
            file_name=r.file_name,
            status=r.status,
            uploaded_at=r.uploaded_at,
        )
        for r in rows
    ]
