"""Full-text search endpoint backed by Elasticsearch."""

from fastapi import APIRouter, HTTPException, Query

from app.schemas import ErrorResponse, SearchResponse, SearchResult
from app.services.es import search_chunks

router = APIRouter(tags=["search"])


def _to_result(hit: dict) -> SearchResult:
    """Map a raw Elasticsearch hit to the wire ``SearchResult`` shape."""
    src = hit["_source"]
    fragments = hit.get("highlight", {}).get("text")
    return SearchResult(
        chunk_id=src["chunk_id"],
        file_name=src["file_name"],
        page=src["page_number"],
        text=src["text"],
        score=hit["_score"],
        highlight=fragments[0] if fragments else None,
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Full-text search",
    description=(
        "Search indexed document chunks with a Russian-analyzed `multi_match` "
        "over the chunk text. Results are score-ordered and highlighted."
    ),
    responses={400: {"model": ErrorResponse, "description": "Empty query"}},
)
async def search(
    q: str = Query(..., description="Search query"),
    from_: int = Query(0, alias="from", ge=0, description="Pagination offset"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
) -> SearchResponse:
    """Search indexed chunks, returning score-ordered, highlighted results."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query 'q' must not be empty")

    total, hits = search_chunks(q, from_, size)
    return SearchResponse(total=total, results=[_to_result(h) for h in hits])
