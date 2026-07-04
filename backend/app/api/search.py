"""Full-text search endpoint backed by Elasticsearch with a Redis result cache."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models import SearchQuery, User
from app.schemas import ErrorResponse, SearchHistoryItem, SearchResponse, SearchResult
from app.services import cache
from app.services.es import SearchHit, search_chunks

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])


def _record_history(db: Session, query: str, results_count: int) -> None:
    """Best-effort persist of a search into history; never fails the request."""
    try:
        db.add(SearchQuery(query=query, results_count=results_count))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to record search history for %r", query)


def _to_result(hit: SearchHit) -> SearchResult:
    """Map a service-layer search hit to the wire ``SearchResult`` shape."""
    return SearchResult(
        chunk_id=hit.chunk_id,
        file_name=hit.file_name,
        page=hit.page,
        text=hit.text,
        score=hit.score,
        highlight=hit.highlight,
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Full-text search",
    description=(
        "Search indexed document chunks with a Russian-analyzed `multi_match` "
        "over the chunk text. Results are score-ordered and highlighted; "
        "identical queries are served from a 5-minute Redis cache."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Empty query"},
        404: {"model": ErrorResponse, "description": "Route not found"},
        422: {"model": ErrorResponse, "description": "Invalid pagination parameters"},
        500: {"model": ErrorResponse, "description": "Elasticsearch or server error"},
    },
)
async def search(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    q: str = Query(..., description="Search query"),
    from_: int = Query(0, alias="from", ge=0, description="Pagination offset"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
) -> SearchResponse:
    """Search indexed chunks, returning score-ordered, highlighted results."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query 'q' must not be empty")

    cached = cache.get_cached(q, from_, size)
    if cached is not None:
        return SearchResponse(**cached)

    total, hits = search_chunks(q, from_, size)
    response = SearchResponse(total=total, results=[_to_result(h) for h in hits])
    cache.set_cached(q, from_, size, response.model_dump())
    # History = one row per first-page query. Skip pagination (from_>0) so a
    # single user search isn't duplicated; cache hits already returned above.
    if from_ == 0:
        _record_history(db, q, total)
    return response


@router.get(
    "/search/history",
    response_model=list[SearchHistoryItem],
    summary="Recent search history",
    description="Return the most recent search queries, newest first.",
    responses={422: {"model": ErrorResponse, "description": "Invalid limit"}},
)
async def search_history(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100, description="Max number of entries to return"),
) -> list[SearchHistoryItem]:
    """Return the newest ``limit`` search-history entries (may be empty)."""
    rows = db.scalars(
        select(SearchQuery).order_by(SearchQuery.created_at.desc()).limit(limit)
    ).all()
    return [
        SearchHistoryItem(query=r.query, results_count=r.results_count, created_at=r.created_at)
        for r in rows
    ]
