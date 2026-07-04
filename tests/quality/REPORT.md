# QA-05 — Search quality (Precision@3)

**Method:** 10 reference queries, each with one known-relevant document. A query
*hits* if its expected document appears in the top-3 results of `GET /search`.
`Precision@3 = hits / 10`.

**Run:** `HOST=http://localhost:8000 python tests/quality/precision_at_3.py`
(regenerates the table below).

| # | Query | Expected doc | Position | Hit@3 |
|---|---|---|---|---|
| 1 | knowledge base sample | `ok.pdf` | 1 | ✅ |
| 2 | searchable docx content | `ok.docx` | 2 | ✅ |
| 3 | elasticsearch relevance | `ok.pdf` | 1 | ✅ |
| 4 | chunk boundaries | `ok.docx` | 2 | ✅ |
| 5 | machine learning lecture | `ml-lecture.pdf` | — | ❌ |
| 6 | exam schedule spring | `schedule.pdf` | — | ❌ |
| 7 | scholarship application form | `scholarship.docx` | — | ❌ |
| 8 | thesis submission guidelines | `thesis-guide.pdf` | — | ❌ |
| 9 | library opening hours | `library.pdf` | — | ❌ |
| 10 | course registration deadline | `registration.docx` | — | ❌ |

**Precision@3 = 4/10 = 0.40**

## Commentary on the misses

The 6 misses are **not a ranking failure** — they are an artifact of the mock.
The current `/search` returns a fixed pair (`ok.pdf`, `ok.docx`) for every query,
so by construction only the 4 queries whose expected document is one of those two
can hit; the other 6 can never match. The 0.40 is thus an **upper bound imposed
by the mock**, not a measurement of relevance.

The value of this stage is the **golden set + harness**: queries 5–10 already
encode realistic ground truth (lecture / schedule / scholarship / thesis /
library / registration documents). Once BE wires real Elasticsearch indexing,
re-running the same script yields a genuine Precision@3 over the real ranker —
no methodology change needed, only the expected documents must exist in the index.
