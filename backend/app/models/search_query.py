"""SQLAlchemy ORM model for saved search-query history."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.document import Base

__all__ = ["SearchQuery"]


class SearchQuery(Base):
    """One recorded user search (first page only — see ``app/api/search.py``).

    Attributes:
        id: Server-generated UUID primary key.
        query: Raw query string as the user typed it.
        results_count: Total ES matches at the time of the search.
        created_at: DB-side UTC timestamp of when the row was written.
    """

    __tablename__ = "search_queries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    query: Mapped[str] = mapped_column(String(1024), nullable=False)
    results_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
