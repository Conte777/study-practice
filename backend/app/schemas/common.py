from pydantic import BaseModel

from app.models.document import DocumentStatus

__all__ = ["DocumentStatus", "ErrorResponse"]


class ErrorResponse(BaseModel):
    """Uniform error body returned by the API's global exception handlers."""

    detail: str
