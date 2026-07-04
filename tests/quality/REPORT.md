# QA-05 — Search quality (Precision@3)

**Method:** 10 reference queries, each with one known-relevant document. A query
*hits* if its expected document appears in the top-3 results of `GET /search`.
`Precision@3 = hits / 10`.

**Target:** real backend — Elasticsearch `multi_match` ranking over the seeded
golden set (not a mock). `/search` requires auth; the harness logs in as the
demo user first.

**Reproduce:**

```
docker compose up -d
uv run --with reportlab --with python-docx python tests/fixtures/generate.py
HOST=http://localhost:8000 python tests/quality/seed.py          # upload + index golden docs
HOST=http://localhost:8000 python tests/quality/precision_at_3.py  # regenerates the table below
```

| # | Query | Expected doc | Position | Hit@3 |
|---|---|---|---|---|
| 1 | knowledge base sample | `ok.pdf` | 1 | ✅ |
| 2 | searchable docx content | `ok.docx` | 1 | ✅ |
| 3 | elasticsearch relevance | `ok.pdf` | 1 | ✅ |
| 4 | chunk boundaries | `ok.docx` | 1 | ✅ |
| 5 | machine learning lecture | `ml-lecture.pdf` | 1 | ✅ |
| 6 | exam schedule spring | `schedule.pdf` | 1 | ✅ |
| 7 | scholarship application form | `scholarship.docx` | 1 | ✅ |
| 8 | thesis submission guidelines | `thesis-guide.pdf` | 1 | ✅ |
| 9 | library opening hours | `library.pdf` | 1 | ✅ |
| 10 | course registration deadline | `registration.docx` | 1 | ✅ |

**Precision@3 = 10/10 = 1.00**

## Commentary

Every expected document ranks **first**, not merely inside the top-3. The golden
set is seeded with one topical document per query (see `tests/fixtures/generate.py`
`write_golden`), so BM25 over the Russian-analyzed `text` field cleanly separates
them — no query is ambiguous between two golden docs.

This is an upper-bound-friendly corpus (8 golden documents serving 10 queries —
queries 1–4 reuse `ok.pdf`/`ok.docx`, the rest map one-to-one), one clear match
each: 1.00
demonstrates the ranker and indexing pipeline work end-to-end, not that ranking
is hard here. The reusable value is the harness + golden set — add noisier or
overlapping documents to the index and re-run to measure precision under
realistic ambiguity without changing the method.
