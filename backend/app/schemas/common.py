from enum import StrEnum

from pydantic import BaseModel


class DocumentStatus(StrEnum):
    """Lifecycle stage of an uploaded document."""

    uploaded = "uploaded"
    indexing = "indexing"
    indexed = "indexed"
    error = "error"


class ErrorResponse(BaseModel):
    """Uniform error body returned by the API's global exception handlers."""

    detail: str
