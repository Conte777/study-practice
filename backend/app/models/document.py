"""SQLAlchemy ORM model for uploaded documents."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.enums import DocumentStatus

__all__ = ["Base", "Document", "DocumentStatus"]


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Document(Base):
    """A user-uploaded document tracked through the upload → index lifecycle.

    Attributes:
        id: Server-generated UUID primary key.
        file_name: Original client-supplied filename.
        status: Lifecycle stage (uploaded → indexing → indexed, or error).
        uploaded_at: UTC timestamp of when the row was created.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        String(16), nullable=False, default=DocumentStatus.uploaded
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
