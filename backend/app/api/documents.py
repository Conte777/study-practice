"""Document endpoints: upload (with content/size validation) and listing."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models import Document, DocumentStatus, User
from app.schemas import DocumentInfo, DocumentUploadResponse, ErrorResponse
from app.services.pipeline import process_document
from app.services.uploads import InvalidUploadError, save_upload, unlink

router = APIRouter(prefix="/documents", tags=["documents"])


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
    _user: Annotated[User, Depends(get_current_user)],
) -> DocumentInfo:
    """Validate an uploaded document, persist its metadata, and return it.

    Parsing, chunking, and Elasticsearch indexing run in a background task so
    the response isn't blocked on them; the document's ``status`` progresses
    from ``uploaded`` to ``indexing``/``indexed`` (or ``error``) as that runs.
    """
    try:
        path, file_type = await save_upload(file)
    except InvalidUploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    doc = Document(
        id=uuid4(),
        file_name=file.filename or "unnamed",
        status=DocumentStatus.uploaded,
    )
    try:
        db.add(doc)
        db.commit()  # expire_on_commit=False: doc's fields (incl. server defaults) stay usable
    except Exception:
        unlink(path)  # nothing will run the background job to clean this up
        raise
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
