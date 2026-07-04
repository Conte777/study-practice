# QA-04 — Load test report

**Scenario:** 50 concurrent users, ramp 10/s, 1 min, search queries.
**Command:** `locust -f loadtest.py --headless -u 50 -r 10 -t 1m --host http://localhost:8000`
**Target:** mock backend (`app.main`) — see the Redis note below on why the numbers are optimistic.

## Result (aggregated)

| Metric | Value |
|---|---|
| Requests | 2251 |
| Failures | **0 (0.00%)** |
| Throughput | ~39.4 req/s |
| Response time p50 | 2 ms |
| Response time p95 | 3 ms |
| Response time p99 | 8 ms |
| Max | 24 ms |

Per-endpoint (all 0 failures):

| Name | # reqs | p50 | p95 | p99 |
|---|---|---|---|---|
| `/search [hot]` (repeated queries) | 1488 | 2 ms | 3 ms | 8 ms |
| `/search [unique]` (cache-busting) | 374 | 2 ms | 3 ms | 7 ms |
| `/search [page2]` (pagination) | 389 | 2 ms | 4 ms | 9 ms |

Throughput is think-time-bound (`wait_time = between(0.5, 2.0)`), i.e. it models
50 humans, not 50 hammers. Drop `wait_time` to measure raw endpoint ceiling.

## Redis-cache influence

The current `/search` is a **mock with no Elasticsearch or Redis** — every
response is built in-process, so the `hot` (repeated → cache-hit) and `unique`
(cache-miss) buckets show **identical latency (~2 ms p50 / 3 ms p95)**. The
cache effect is therefore **not observable yet**.

The `hot` vs `unique` task split is the instrument to measure it once BE wires
ES + Redis: `hot` will report the warm-cache path (low, stable p95), `unique`
the cold ES path (higher, more variable). Re-run this gate after that stage and
compare the two rows — a widening gap quantifies the cache's contribution.
