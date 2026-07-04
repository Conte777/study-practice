# Архитектура

Full-stack поиск по документам. Этот документ описывает сервисы, поток данных,
аутентификацию, контракт API и мониторинг. Полная спецификация эндпоинтов —
Swagger на `/docs`; краткий обзор — [`backend/README.md`](../backend/README.md).

## Сервисы

7 контейнеров (`docker-compose.yml`):

| Сервис | Образ / стек | Роль |
|---|---|---|
| `app` | FastAPI + SQLAlchemy 2 | REST API `/api/v1`, парсинг/индексация, `/metrics` |
| `front` | React 19 + Vite + nginx | UI (порт 8080), прокси `/api/` → `app:8000` |
| `postgres` | postgres:16 | документы, пользователи, история поиска |
| `elasticsearch` | elasticsearch:8.15 | индекс `documents` (по чанку на запись) |
| `redis` | redis:7 | кэш результатов поиска |
| `prometheus` | prom/prometheus | скрейп `app:8000/metrics` |
| `grafana` | grafana:11 | дашборд RPS/латентности поиска |

## Поток данных: загрузка → индексация

`backend/app/api/documents.py` + `backend/app/services/{uploads,parser,chunker,es,pipeline}.py`.

1. **Валидация** (`uploads.save_upload`): файл стримится на диск чанками по 1 МиБ,
   тип определяется по **сигнатуре содержимого**, не по расширению (`%PDF` → pdf;
   `PK\x03\x04` + запись `word/` в zip → docx). Отсев: пустой файл, > 20 МБ,
   неподдерживаемый тип → `InvalidUploadError` → HTTP 400.
2. **Ответ сразу**: метаданные пишутся в Postgres со статусом `uploaded`, дальше —
   `BackgroundTasks`, клиент не блокируется на индексации.
3. **Парсинг** (`parser.extract_text`): `pdfplumber` (PDF, по страницам) или
   `python-docx` (DOCX). Битый вход не падает — возвращает `[]`.
4. **Чанкинг** (`chunker.chunk_text`): фикс-окно 1000 символов с перекрытием 100.
5. **Индексация** (`es.index_document`): bulk в индекс `documents`, russian-analyzer
   на поле `text`. Идемпотентно: `_id = f"{document_id}:{i}"`, повторная индексация
   перезаписывает, а не дублирует.
6. **Статус** прогрессирует `uploaded → indexing → indexed`; любая ошибка пайплайна
   переводит документ в `error`, не роняя воркер (`pipeline.process_document`).

## Поиск

`backend/app/api/search.py` + `backend/app/services/{es,cache}.py`.

- `GET /api/v1/search?q=&from=&size=` — `multi_match` по полю `text`,
  `<mark>`-подсветка фрагментов, пагинация `from/size` (size 1..100).
- **Кэш** (`cache.py`): Redis, ключ нормализован (lowercase + схлопывание
  пробелов), TTL 300 с. Redis недоступен → тихая деградация, отдаём живой ответ ES.
- **История** (`GET /api/v1/search/history`): по строке на запрос первой страницы
  (`from == 0`), best-effort — сбой записи не валит поиск.

## Аутентификация

`backend/app/api/auth.py`, `backend/app/core/{security,seed}.py`.

- JWT HS256 (`JWT_SECRET`, срок `JWT_EXPIRE_MINUTES`), пароли — bcrypt.
- `register`/`login` возвращают bearer-токен; `get_current_user` — зависимость-guard
  на всех эндпоинтах документов и поиска.
- Login сверяет пароль даже при отсутствующем юзере (dummy-hash), чтобы тайминг
  не выдавал наличие логина.
- Demo-user сидится при старте (`seed_demo_user`, `DEMO_USER`/`DEMO_PASSWORD`;
  пустой `DEMO_USER` отключает сидинг).

## Контракт API

Источник правды — Pydantic-схемы `backend/app/schemas/`. Из них FastAPI генерит
OpenAPI (`/docs`, `/openapi.json`), а `frontend/src/types/api.ts` — **ручное
зеркало** этих схем. Расхождение ловит `backend/tests/test_contract.py`: меняешь
схему — обновляешь TS-типы. (Этот раздел — наследник удалённого `CONTRACTS.md`.)

## Мониторинг

DO-06. `app` экспонирует `GET /metrics` (`prometheus-fastapi-instrumentator`,
**вне** префикса `/api/v1`) с дефолтными `http_requests_total` и
`http_request_duration_seconds`, размеченными по хендлеру — отсюда RPS и
латентность `/search`.

- **Prometheus** скрейпит `app:8000/metrics` (`monitoring/prometheus.yml`).
- **Grafana** (`http://localhost:${GRAFANA_PORT}`, admin/`${GRAFANA_ADMIN_PASSWORD}`)
  провижинится автоматически: datasource + дашборд из
  `monitoring/grafana/provisioning/`, сам дашборд — `monitoring/grafana/dashboards/search.json`.

## Известные ограничения

- **DOCX всегда page 1**: в XML нет понятия страницы, все параграфы — одна
  логическая страница (upgrade: рендер в PDF через LibreOffice).
- **Только russian-analyzer** на поле `text` (upgrade: `analysis-morphology`).
- **Нет миграций** (нет Alembic): схема создаётся при старте `init_db()`
  (`create_all`), demo-user — `seed_demo_user()`.
- **Graceful degradation**: недоступность ES при старте и Redis в рантайме
  логируется, но не роняет приложение.
