# ponytail: uv image already gives us layer-cached deps + reproducible venv — no need for a
# separate build stage. Non-root added below for DO-01.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# deps layer: cached until pyproject/uv.lock change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
ENV PATH="/app/.venv/bin:$PATH"

# non-root: own the workdir, then drop privileges
RUN useradd --system --uid 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
