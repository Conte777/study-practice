from enum import StrEnum

from pydantic import BaseModel


class DocumentStatus(StrEnum):
    uploaded = "uploaded"
    indexing = "indexing"
    indexed = "indexed"
    error = "error"


class ErrorResponse(BaseModel):
    detail: str
