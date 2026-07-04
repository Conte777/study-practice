"""Redis-backed cache for search results.

Keys are normalized (lowercased, whitespace-collapsed) so that queries
differing only in case or spacing share a cache entry. Every Redis operation
degrades gracefully: if Redis is unreachable, cache reads return ``None`` and
writes are dropped, so search still serves live results from Elasticsearch.
"""

import json
import logging
from functools import lru_cache

import redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

TTL_SECONDS = 300


@lru_cache(maxsize=1)
def get_client() -> redis.Redis:
    """Return a process-wide Redis client built from settings."""
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _key(q: str, from_: int, size: int) -> str:
    normalized = " ".join(q.lower().split())
    return f"search:{normalized}:{from_}:{size}"


def get_cached(q: str, from_: int, size: int) -> dict | None:
    """Return a cached search response, or ``None`` on miss or Redis failure."""
    try:
        raw = get_client().get(_key(q, from_, size))
    except RedisError:
        # ponytail: broad RedisError catch = graceful degradation. Search falls
        # back to Elasticsearch; a down cache must never surface as a 500.
        logger.warning("Redis unavailable on cache read; serving from Elasticsearch")
        return None
    return json.loads(raw) if raw else None


def set_cached(q: str, from_: int, size: int, value: dict) -> None:
    """Store a search response with a 300s TTL; drop silently if Redis is down."""
    try:
        get_client().set(_key(q, from_, size), json.dumps(value), ex=TTL_SECONDS)
    except RedisError:
        logger.warning("Redis unavailable on cache write; result not cached")
