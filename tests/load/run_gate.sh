#!/usr/bin/env bash
# QA-04 gate: 50 concurrent users hitting /search for 1 minute.
# Needs a running backend at $HOST (default http://localhost:8000).
set -euo pipefail
cd "$(dirname "$0")"

HOST="${HOST:-http://localhost:8000}"
mkdir -p report

# locust is a QA-only tool — run it ephemerally, don't pollute backend deps.
uv run --with locust locust -f loadtest.py --headless \
  -u 50 -r 10 -t 1m \
  --host "$HOST" \
  --csv report/search --only-summary "$@"

echo "CSV stats written to tests/load/report/*.csv — summary above."
