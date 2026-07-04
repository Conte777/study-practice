#!/usr/bin/env bash
# ponytail: one-shot local dev bootstrap (deps + hooks). For data seeding use ./init.sh.
set -euo pipefail

[ -f .env ] || cp .env.example .env

echo "== backend =="
(cd backend && uv sync)

echo "== pre-commit hooks =="
./backend/.venv/bin/pre-commit install  # config auto-detected at repo root

echo "== frontend =="
(cd frontend && npm install)

echo "Done. Run backend:  cd backend && uv run uvicorn app.main:app --reload"
echo "     Run frontend: cd frontend && npm run dev"
echo "     Or full stack: docker compose up --build"
