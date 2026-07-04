from fastapi import APIRouter, HTTPException, Query

from app.schemas import ErrorResponse, SearchResponse, SearchResult

router = APIRouter(tags=["search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    responses={400: {"model": ErrorResponse}},
)
async def search(
    q: str = Query(..., description="Search query"),
    from_: int = Query(0, alias="from", ge=0),
    size: int = Query(10, ge=1, le=100),
) -> SearchResponse:
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query 'q' must not be empty")

    # mock: BE stage 4 replaces with Elasticsearch query. highlight = ES pre/post-tags <mark>.
    results = [
        SearchResult(
            chunk_id="chunk-1",
            file_name="ok.pdf",
            page=1,
            text=f"This is a sample passage matching {q} in the knowledge base.",
            score=1.42,
            highlight=f"This is a sample passage matching <mark>{q}</mark> in the knowledge base.",
        ),
        SearchResult(
            chunk_id="chunk-2",
            file_name="ok.docx",
            page=3,
            text=f"Another chunk that mentions {q} with lower relevance.",
            score=0.87,
            highlight=f"Another chunk that mentions <mark>{q}</mark> with lower relevance.",
        ),
    ]
    return SearchResponse(total=len(results), results=results)
