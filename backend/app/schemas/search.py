from datetime import datetime

from pydantic import BaseModel


class SearchHistoryItem(BaseModel):
    """One past search, newest-first in the history listing."""

    query: str
    results_count: int
    created_at: datetime


class SearchResult(BaseModel):
    """One matched chunk from a search query."""

    chunk_id: str
    file_name: str
    page: int
    text: str
    score: float
    # Same fragment as `text` with <mark>…</mark> around matches (ES highlight,
    # pre/post-tags <mark>). null when no highlight — FE falls back to `text`.
    # FE sanitizes before rendering.
    highlight: str | None = None


class SearchResponse(BaseModel):
    """A page of search results with the total match count."""

    total: int  # FE-07 pagination
    results: list[SearchResult]
