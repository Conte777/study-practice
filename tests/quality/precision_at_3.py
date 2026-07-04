#!/usr/bin/env python3
"""QA-05 — search quality: Precision@3 over a golden query set.

For 10 reference queries with a known expected document, check whether that
document lands in the top-3 results, then print a Markdown table + the metric.

Run (backend up, golden set seeded via tests/quality/seed.py):
    HOST=http://localhost:8000 python tests/quality/precision_at_3.py

/search requires auth, so this logs in as the demo user first and sends the
bearer token with each query.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass

HOST = os.environ.get("HOST", "http://localhost:8000").rstrip("/")
USER = os.environ.get("DEMO_USER", "demo")
PASSWORD = os.environ.get("DEMO_PASSWORD", "demo12345")
TOP_K = 3


def login() -> str:
    """Return a bearer token for the demo account."""
    body = json.dumps({"username": USER, "password": PASSWORD}).encode()
    req = urllib.request.Request(
        f"{HOST}/api/v1/auth/login", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 (trusted local host)
        return json.load(resp)["access_token"]


@dataclass(frozen=True)
class Golden:
    query: str
    expected_file: str


# 10 reference queries ↔ the document that SHOULD rank in the top-3.
# Expected files are the ground truth for the real index; on the mock only
# ok.pdf / ok.docx are ever returned (see module docstring).
GOLDEN: list[Golden] = [
    Golden("knowledge base sample", "ok.pdf"),
    Golden("searchable docx content", "ok.docx"),
    Golden("elasticsearch relevance", "ok.pdf"),
    Golden("chunk boundaries", "ok.docx"),
    Golden("machine learning lecture", "ml-lecture.pdf"),
    Golden("exam schedule spring", "schedule.pdf"),
    Golden("scholarship application form", "scholarship.docx"),
    Golden("thesis submission guidelines", "thesis-guide.pdf"),
    Golden("library opening hours", "library.pdf"),
    Golden("course registration deadline", "registration.docx"),
]


def search(query: str, token: str) -> list[str]:
    """Return the ordered list of result file_names for a query."""
    qs = urllib.parse.urlencode({"q": query, "size": TOP_K})
    req = urllib.request.Request(
        f"{HOST}/api/v1/search?{qs}", headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 (trusted local host)
        body = json.load(resp)
    return [r["file_name"] for r in body["results"]]


def position_of(expected: str, files: list[str]) -> int | None:
    """1-based rank of `expected`, or None if absent."""
    for i, name in enumerate(files, start=1):
        if name == expected:
            return i
    return None


def main() -> int:
    token = login()
    rows = []
    hits = 0
    for g in GOLDEN:
        try:
            files = search(g.query, token)
        except Exception as exc:  # noqa: BLE001 — surface any transport error in the table
            rows.append((g.query, g.expected_file, f"ERROR: {exc}", False))
            continue
        pos = position_of(g.expected_file, files[:TOP_K])
        hit = pos is not None
        hits += hit
        rows.append((g.query, g.expected_file, str(pos) if pos else "—", hit))

    precision = hits / len(GOLDEN)

    print(f"# QA-05 — Precision@{TOP_K}\n")
    print(f"Host: `{HOST}`  ·  queries: {len(GOLDEN)}\n")
    print(f"| # | Query | Expected doc | Position | Hit@{TOP_K} |")
    print("|---|---|---|---|---|")
    for i, (q, exp, pos, hit) in enumerate(rows, start=1):
        print(f"| {i} | {q} | `{exp}` | {pos} | {'✅' if hit else '❌'} |")
    print(f"\n**Precision@{TOP_K} = {hits}/{len(GOLDEN)} = {precision:.2f}**")

    if precision < 1.0:
        miss = [r[0] for r in rows if not r[3]]
        print(
            f"\n> {len(miss)} miss(es): {', '.join(miss)}.\n"
            "> Ensure the golden set is seeded (tests/quality/seed.py) and indexed."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
