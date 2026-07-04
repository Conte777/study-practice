from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from app.schemas import DocumentInfo, DocumentStatus, DocumentUploadResponse, ErrorResponse

router = APIRouter(prefix="/documents", tags=["documents"])

# ponytail: upload-mock validates content-type/size (real, cheap, gives FE the 400 case),
# but does not parse or index — that's BE stages 2/3.
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_SIZE_BYTES = 20 * 1024 * 1024  # ТЗ: 20 МБ limit


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    responses={400: {"model": ErrorResponse}},
)
async def upload_document(file: UploadFile) -> DocumentUploadResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    size = len(await file.read())
    if size == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if size > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 20 MB limit")

    return DocumentInfo(
        id=uuid4(),
        file_name=file.filename or "unnamed",
        status=DocumentStatus.uploaded,
        uploaded_at=datetime.now(UTC),
    )


@router.get("", response_model=list[DocumentInfo])
async def list_documents() -> list[DocumentInfo]:
    # mock: BE stage replaces with DB query
    return [
        DocumentInfo(
            id=uuid4(),
            file_name="ok.pdf",
            status=DocumentStatus.indexed,
            uploaded_at=datetime.now(UTC),
        ),
        DocumentInfo(
            id=uuid4(),
            file_name="ok.docx",
            status=DocumentStatus.indexing,
            uploaded_at=datetime.now(UTC),
        ),
    ]
