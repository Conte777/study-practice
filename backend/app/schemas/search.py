from pydantic import BaseModel


class SearchResult(BaseModel):
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
    total: int  # FE-07 pagination
    results: list[SearchResult]
