"""QA-04 — load test: 50 concurrent users issuing search queries.

Run (from this dir), matching the QA gate:
    locust -f loadtest.py --headless -u 50 -r 10 -t 1m --host http://localhost:8000

Report (p50/p95, RPS, error %) is printed by Locust and also written to
`report/` CSVs when `--csv report/search` is passed (see run_gate.sh).

Redis-cache note: `/search` results are cached (BE stage). Reusing a small set
of hot queries measures the *warm-cache* path (optimistic p95); `unique_query`
forces cache misses to expose the cold path. Keep both to bracket real latency.
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task

# Hot set — repeated across users, so mostly Redis cache hits (warm path).
HOT_QUERIES = [
    "machine learning",
    "database indexing",
    "final exam schedule",
    "scholarship application",
    "thesis submission",
]


class SearchUser(HttpUser):
    # Think time between requests — models a human reading results, not a hammer.
    wait_time = between(0.5, 2.0)

    @task(4)
    def search_hot(self) -> None:
        q = random.choice(HOT_QUERIES)
        # name= groups all hot queries into one row regardless of q value.
        self.client.get("/api/v1/search", params={"q": q}, name="/search [hot]")

    @task(1)
    def search_unique(self) -> None:
        # Cache-busting query → cold path (no Redis hit).
        q = f"query-{random.randint(0, 1_000_000)}"
        self.client.get("/api/v1/search", params={"q": q}, name="/search [unique]")

    @task(1)
    def search_paginated(self) -> None:
        q = random.choice(HOT_QUERIES)
        self.client.get(
            "/api/v1/search",
            params={"q": q, "from": 10, "size": 10},
            name="/search [page2]",
        )
