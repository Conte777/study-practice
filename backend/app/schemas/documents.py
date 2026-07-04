from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import DocumentStatus


class DocumentInfo(BaseModel):
    id: UUID
    file_name: str
    status: DocumentStatus
    uploaded_at: datetime


# Upload returns the same shape as a list item — kept as an alias for contract clarity.
DocumentUploadResponse = DocumentInfo
