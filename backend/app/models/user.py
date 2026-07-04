"""SQLAlchemy ORM model for authentication users."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.document import Base

__all__ = ["User"]


class User(Base):
    """A login account. No roles — auth is presence-of-valid-token only.

    Attributes:
        id: Server-generated UUID primary key.
        username: Unique login handle.
        password_hash: bcrypt hash; the plaintext is never stored.
        created_at: DB-side UTC timestamp of account creation.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
