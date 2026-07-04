# Backend — API поиска по базе знаний

FastAPI + SQLAlchemy 2, пакетный менеджер **uv**. Все команды — из `backend/`.

## Эндпоинты (`/api/v1`)

| Метод + путь | Auth | Назначение |
|---|---|---|
| `POST /auth/register` | — | создать аккаунт, вернуть токен (409 если занят) |
| `POST /auth/login` | — | вернуть bearer-токен (401 при неверных данных) |
| `POST /documents/upload` | ✅ | загрузка PDF/DOCX (валидация тип+размер), фоновая индексация |
| `GET /documents` | — | список документов, новые сверху |
| `GET /search?q=&from=&size=` | ✅ | полнотекстовый поиск с подсветкой |
| `GET /search/history` | ✅ | последние запросы |
| `GET /health` | — | liveness |
| `GET /metrics` | — | Prometheus (вне `/api/v1`) |

Полная спека — Swagger `/docs`. Поток данных — [`../docs/architecture.md`](../docs/architecture.md).

## Запуск

```bash
uv sync
uv run uvicorn app.main:app --reload    # → http://localhost:8000/docs
```

## Тесты и линт

```bash
uv run pytest -q --cov=app --cov-report=term-missing --cov-fail-under=50  # gate 50% в CI
uv run ruff check
uv run ruff format --check
```

Unit- и contract-тесты идут на sqlite (Postgres не нужен — `conftest.py` выставляет
env до импорта приложения). Integration-тесты (`pytestmark = pytest.mark.integration`)
gracefully скипаются без живых ES/Redis; чтобы гонять их по-настоящему, откройте
порты через `docker-compose.override.yml`.
