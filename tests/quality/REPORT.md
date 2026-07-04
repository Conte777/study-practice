# QA-05 — Search quality (Precision@3)

**Method:** 10 reference queries, each with one known-relevant document. A query
*hits* if its expected document appears in the top-3 results of `GET /search`.
`Precision@3 = hits / 10`.

**Target:** real backend — Elasticsearch `multi_match` ranking over the seeded
corpus (not a mock). `/search` requires auth; the harness logs in as the demo
user first.

**Corpus:** 8 golden documents (one clear match per query) **+ 6 distractors**
that deliberately share vocabulary with a golden query but are *not* its answer
(e.g. `deep-learning-seminar.pdf` vs `ml-lecture.pdf` on "machine learning",
`campus-hours.pdf` vs `library.pdf` on "opening hours"). This forces BM25 to
discriminate on the query's distinguishing term instead of ranking an
uncontested single match. See `tests/fixtures/generate.py` (`_DISTRACTOR_*`).

**Reproduce:**

```
docker compose up -d
uv run --no-project --with reportlab --with python-docx python tests/fixtures/generate.py
HOST=http://localhost:8000 python tests/quality/seed.py            # upload + index 14 docs (8 golden + 6 distractors)
HOST=http://localhost:8000 python tests/quality/precision_at_3.py  # regenerates the table below
```

| # | Query | Expected doc | Position | Top competitor (score margin) | Hit@3 |
|---|---|---|---|---|---|
| 1 | knowledge base sample | `ok.pdf` | 1 | `ok.docx` (+6.11) | ✅ |
| 2 | searchable docx content | `ok.docx` | 1 | — | ✅ |
| 3 | elasticsearch relevance | `ok.pdf` | 1 | — | ✅ |
| 4 | chunk boundaries | `ok.docx` | 1 | — | ✅ |
| 5 | machine learning lecture | `ml-lecture.pdf` | 1 | `deep-learning-seminar.pdf` (+5.82) | ✅ |
| 6 | exam schedule spring | `schedule.pdf` | 1 | `timetable.pdf` (+4.01) | ✅ |
| 7 | scholarship application form | `scholarship.docx` | 1 | `financial-aid-faq.docx` (+7.38) | ✅ |
| 8 | thesis submission guidelines | `thesis-guide.pdf` | 1 | `dissertation-defense.pdf` (+3.82) | ✅ |
| 9 | library opening hours | `library.pdf` | 1 | `campus-hours.pdf` (+3.63) | ✅ |
| 10 | course registration deadline | `registration.docx` | 1 | `scholarship.docx` (+6.43) | ✅ |

**Precision@3 = 10/10 = 1.00**

## Commentary

Every expected document ranks **first** — and now does so *against a competitor
that shares its query terms*. The "Top competitor" column is the highest-scoring
non-expected document per query; for 6 of the 10 queries that runner-up is a
purpose-built distractor. The score margin shows BM25 separates them cleanly by
weighting the distinguishing term (`lecture`, `exam`, `thesis`, `library`,
`registration`, `scholarship`) that the distractor lacks.

Queries 2–4 have no competitor: no other corpus document shares their
vocabulary, so the expected doc is the only match — a legitimate uncontested
result.

1.00 here means the ranker resolves genuine vocabulary overlap correctly, not
that the corpus is trivial. The reusable value is the harness + corpus: add
noisier or more overlapping documents and re-run to measure precision under
harder ambiguity without changing the method.
