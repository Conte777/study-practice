# CONTRACTS — единый свод межкомандных швов

Единая точка для BE / FE / DO / QA. **При изменении контракта правятся Pydantic-схемы
(`backend/app/schemas/`) И этот файл.** OpenAPI (`/docs`, `/openapi.json`) генерируется из схем —
истина в коде, здесь — человекочитаемое зеркало.

## API

Base URL: `http://localhost:8000/api/v1` (`VITE_API_BASE_URL`).

| Метод / путь | Запрос | 200 | Ошибка | ТЗ |
|---|---|---|---|---|
| `POST /documents/upload` | multipart `file` | `DocumentUploadResponse` | 400 `ErrorResponse` | BE-01/02/03, FE-02 |
| `GET /documents` | — | `list[DocumentInfo]` | — | FE-03 |
| `GET /search` | `q`, `from`=0, `size`=10 | `SearchResponse` | 400 при пустом `q` | BE-08/09, FE-04/07 |
| `GET /health` | — | `{"status":"ok"}` | — | DO healthcheck |

Пагинация — `from`/`size` (query). `SearchResponse.total` — для FE-07.

### Схемы (см. `backend/app/schemas/`, зеркало `frontend/src/types/api.ts`)

- `ErrorResponse { detail: str }` — единое тело для 400/404/500.
- `DocumentInfo { id: UUID, file_name: str, status: DocumentStatus, uploaded_at: datetime }`.
  `DocumentUploadResponse` = `DocumentInfo`.
- `SearchResult { chunk_id, file_name, page, text, score, highlight: str|null }`.
  `highlight` — тот же фрагмент с `<mark>…</mark>` (ES pre/post-tags `<mark>`); `null` → FE фолбэк на `text`.
  Санитайзинг HTML — на FE (стадия 4).
- `SearchResponse { total: int, results: SearchResult[] }`.

## Статусы документа (enum) и подписи FE-02

| `DocumentStatus` | Подпись FE |
|---|---|
| `uploaded` | Загрузка… |
| `indexing` | Индексация… |
| `indexed` | Готово |
| `error` | Ошибка |

Маппинг — в `frontend/src/types/api.ts` (`STATUS_LABELS`).

## Окружение (`.env.example`)

Имена сервисов = хосты в compose: `postgres`, `elasticsearch`, `redis`, `app`, `front`.

| Переменная | Назначение |
|---|---|
| `POSTGRES_USER/PASSWORD/DB/HOST/PORT`, `DATABASE_URL` | Postgres |
| `ELASTICSEARCH_URL` | `http://elasticsearch:9200` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `BACKEND_PORT` | `8000` |
| `CORS_ORIGINS` | `http://localhost:8080` (фронт) |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` |

## Тестовые фикстуры (QA ↔ BE)

Манифест имён — `tests/fixtures/README.md`. Имена зашиты в гейты BE, менять только синхронно.

## E2E-селекторы (`data-testid`, QA ↔ FE)

`upload-dropzone`, `upload-item`, `upload-status`, `doc-list`,
`search-input`, `search-button`, `result-card`, `result-file-name`,
`result-page`, `result-score`, `no-results`, `pagination`.
