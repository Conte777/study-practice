# Поиск по базе знаний университета

Full-stack поиск по документам: загрузка PDF/DOCX → парсинг → чанкинг →
индексация в Elasticsearch → полнотекстовый поиск с подсветкой. UI и комментарии
на русском, идентификаторы кода — на английском.

Контракт API держится дисциплиной `backend/app/schemas/` (Pydantic, источник
правды) → OpenAPI (`/docs`) → ручное зеркало `frontend/src/types/api.ts`; guard —
`backend/tests/test_contract.py`. Подробнее — [`docs/architecture.md`](./docs/architecture.md).

## Стек

7 сервисов в `docker-compose.yml`:

| Сервис | Роль |
|---|---|
| `app` | FastAPI + SQLAlchemy 2 (uv), Swagger `/docs`, health `/api/v1/health`, метрики `/metrics` |
| `front` | React 19 + TS + Vite, nginx-прокси `/api/` → `app:8000` (порт 8080) |
| `postgres` | метаданные документов, пользователи, история поиска |
| `elasticsearch` | индекс чанков с russian-analyzer |
| `redis` | кэш результатов поиска (TTL 300 с) |
| `prometheus` | сбор метрик с `app:8000/metrics` |
| `grafana` | дашборд поиска (RPS/латентность) |

Аутентификация — JWT (HS256, bcrypt); demo-user сидится при старте
(`demo`/`demo12345`, настраивается через `.env`).

## Быстрый старт

```bash
./dev-setup.sh                  # .env + зависимости BE/FE + pre-commit
docker compose up --build       # поднять весь стек (7 сервисов)
./init.sh                       # засеять 10 arXiv-PDF в поднятый API (DO-07)
```

Локально без docker:

```bash
cd backend  && uv run uvicorn app.main:app --reload   # → http://localhost:8000/docs
cd frontend && npm run dev                            # → http://localhost:8080
```

UI на `:8080` открывается за login-gate; войдите `demo`/`demo12345`.

## Возможности

- Загрузка PDF/DOCX с валидацией по сигнатуре содержимого (не по расширению),
  лимит 20 МБ, отсев пустых файлов.
- Парсинг: `pdfplumber` (PDF, по страницам), `python-docx` (DOCX).
- Чанкинг фикс-окном 1000 символов с перекрытием 100.
- Индексация в Elasticsearch (russian-analyzer, идемпотентный `_id`), поиск
  `multi_match` с `<mark>`-подсветкой и пагинацией `from/size`.
- Redis-кэш повторных запросов, история поиска.

## Мониторинг

Grafana на `http://localhost:${GRAFANA_PORT}` (по умолчанию `:3000`,
admin/`${GRAFANA_ADMIN_PASSWORD}`). Дашборд — `monitoring/grafana/dashboards/search.json`
(автопровижининг из `monitoring/grafana/provisioning/`), источник — Prometheus,
скрейпящий `app`-эндпоинт `/metrics` (см. `monitoring/prometheus.yml`). Детали —
[`docs/architecture.md`](./docs/architecture.md#мониторинг).

## Структура

```
backend/          FastAPI: app/{api,core,models,schemas,services}/ + main.py; tests/
frontend/         React + Vite: src/{pages,services,types,utils}/ + App.tsx
e2e/              Playwright (smoke + critical-path)
monitoring/       prometheus.yml, grafana/{provisioning,dashboards}/
seed/             PDF, скачанные init.sh (git-ignored)
tests/            QA-артефакты: load/, quality/, fixtures/
docs/             architecture.md, user-guide.md
docker-compose.yml  .env.example  dev-setup.sh  init.sh
```

Дока по компонентам: [`backend/README.md`](./backend/README.md),
[`frontend/README.md`](./frontend/README.md), [`docs/user-guide.md`](./docs/user-guide.md).
