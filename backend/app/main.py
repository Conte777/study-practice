"""FastAPI application entrypoint: routing, CORS, and DB bootstrap."""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import documents, search
from app.core.config import settings
from app.core.db import init_db
from app.services.es import ensure_index

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables and the Elasticsearch index on startup."""
    init_db()
    try:
        ensure_index()
    except Exception:  # noqa: BLE001 — ES may be down; degrade, don't block startup
        logger.exception("Elasticsearch unavailable during startup index bootstrap")
    yield


app = FastAPI(title="University Knowledge Search", version="0.1.0", lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    """Return HTTP errors as the `{"detail": ...}` shape used across the API."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Flatten FastAPI's default validation error list into a single string."""
    detail = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected errors: log the traceback, return a plain 500."""
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# DO-06: default metrics = http_requests_total + http_request_duration_seconds, labelled
# per handler (RPS & latency of /search fall out of this). Exposes GET /metrics.
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api/v1")
api.include_router(documents.router)
api.include_router(search.router)


@api.get("/health", tags=["health"], summary="Health check", description="Liveness probe.")
async def health() -> dict[str, str]:
    """Return a static OK status for liveness probes."""
    return {"status": "ok"}


app.include_router(api)
