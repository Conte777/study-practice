# План: Backend (BE)

**Роль:** разработка REST API, интеграция с Elasticsearch, парсинг документов, кеш.
**Стек:** Python 3.12, FastAPI, SQLAlchemy + PostgreSQL, Elasticsearch (analysis-ru), Redis, pdfplumber, python-docx, pytest.
**Директория:** `backend/` (см. структуру репозитория в ТЗ).

Стадии идут по фичам. Переход на следующую стадию **только после прохождения гейта**.
Гейт = ① runnable-проверка ② чеклист Done (привязка к ID ТЗ) ③ ревью sub-agent'ом.

Как запускать ревью гейта:
> Task(subagent_type="review-code", prompt="Проверь стадию N плана backend/…: соответствие требованиям <ID>, обработка ошибок, edge-cases парсинга/валидации. Верни confirmed-findings.")

---

## Стадия 1 — Каркас + загрузка/валидация (BE-01, BE-02, BE-03)

**Задачи**
- `app/main.py` — FastAPI app, `/docs` (Swagger), health-check.
- `app/core/config.py` — pydantic-settings, чтение из env.
- `app/models/document.py` — SQLAlchemy-модель (uuid, file_name, status, uploaded_at).
- `POST /api/v1/documents/upload` — приём файла.
- Валидация: формат ∈ {PDF, DOCX}, размер ≤ 20 МБ → иначе HTTP 400 с телом `{"detail": "..."}`.
- UUID на каждый документ (BE-03).

**Гейт 1**
- Команда: `curl -F file=@tests/fixtures/ok.pdf localhost:8000/api/v1/documents/upload` → 200 + uuid.
- Команда: `curl -F file=@tests/fixtures/big.bin ...` (25 МБ) → 400 с описанием.
- Команда: `curl -F file=@tests/fixtures/note.txt ...` → 400.
- Чеклист: [ ] BE-01 эндпоинт есть [ ] BE-02 оба кейса 400 [ ] BE-03 uuid уникален [ ] запись в БД создаётся [ ] Swagger `/docs` открывается.
- Ревью: sub-agent review-code — валидация формата по содержимому, а не только по расширению; лимит размера не читает весь файл в память.

---

## Стадия 2 — Извлечение текста + чанкинг (BE-04, BE-05)

**Задачи**
- `app/services/parser.py` — `extract_text(path) -> list[Page]` через pdfplumber (PDF) и python-docx (DOCX), с сохранением `page_number`.
- `app/services/chunker.py` — разбиение на чанки 1000 симв., перекрытие 100 симв. между соседними.
- Пайплайн upload → parse → chunk (пока без индексации).

**Гейт 2**
- Команда: `pytest backend/tests/test_parser.py test_chunker.py -q`.
- Проверка чанкинга: длина каждого чанка ≤ 1000; соседние перекрываются на 100; последние 100 симв. чанка N == первые 100 симв. чанка N+1.
- Чеклист: [ ] BE-04 PDF и DOCX парсятся [ ] page_number проставлен [ ] BE-05 размер/перекрытие точны [ ] пустой файл не роняет пайплайн.
- Ревью: sub-agent review-code — off-by-one в окне перекрытия; поведение на тексте < 1000 симв.; кодировки/битые файлы.

---

## Стадия 3 — Elasticsearch: индекс + индексация (BE-06, BE-07)

**Задачи**
- `app/services/es.py` — клиент ES, создание индекса `documents` с русскоязычным анализатором (analysis-ru) при старте.
- Маппинг: `file_name`, `page_number`, `chunk_id`, `text` (text + ru-analyzer).
- Индексация: каждый чанк → документ ES с метаданными.
- Связать с upload: после чанкинга статус документа → `indexed`.

**Гейт 3**
- Команда: `curl localhost:9200/documents/_count` после загрузки → count == числу чанков.
- Команда: `curl localhost:9200/documents/_mapping` → поля и ru-analyzer присутствуют.
- Чеклист: [ ] BE-06 индекс+analysis-ru создан [ ] BE-07 все чанки с метаданными [ ] переиндексация идемпотентна (нет дублей).
- Ревью: sub-agent review-code — bulk vs поштучная индексация; обработка недоступности ES; корректность analyzer.

---

## Стадия 4 — Поиск (BE-08, BE-09, + API-статусы)

**Задачи**
- `GET /api/v1/search?q={query}` — `multi_match` по полю `text`.
- Ответ JSON: `[{chunk_id, file_name, page, text, score}]`.
- Подсветка: вернуть ES highlight по `text` (FE ждёт совпадения — согласовать формат).
- HTTP-статусы: 200 / 400 (пустой q) / 404 / 500.

**Гейт 4**
- Команда: `curl "localhost:8000/api/v1/search?q=алгоритм"` → массив с полями chunk_id/file_name/page/text/score, отсортирован по score desc.
- Команда: `curl "localhost:8000/api/v1/search?q="` → 400.
- Чеклист: [ ] BE-08 multi_match [ ] BE-09 все поля в ответе [ ] score присутствует [ ] статусы корректны [ ] формат согласован с FE.
- Ревью: sub-agent review-code — инъекция в query-DSL; поведение при 0 результатов; пагинация (from/size) заложена для FE-07.

---

## Стадия 5 — Redis-кеш (BE-10)

**Задачи**
- `app/services/cache.py` — ключ = нормализованный `q`, TTL 5 мин.
- В `/search`: cache-hit → отдать из Redis, минуя ES.

**Гейт 5**
- Команда: два одинаковых запроса подряд; второй — из кеша (проверить логом/метрикой X-Cache или временем ответа).
- Команда: `redis-cli keys 'search:*'` → ключ есть, `ttl` ≤ 300.
- Чеклист: [ ] BE-10 hit/miss работает [ ] TTL=300 [ ] недоступность Redis не роняет поиск (graceful fallback).
- Ревью: sub-agent review-code — нормализация ключа (регистр/пробелы); стойкость к падению Redis.

---

## Стадия 6 — Документация API + чистка (API-требования, критерий «Качество кода»)

**Задачи**
- OpenAPI 3.0: описания эндпоинтов, схемы ответов/ошибок, примеры.
- Docstrings на всех публичных функциях/классах (параметры, возврат) — PEP 8, понятные имена.
- Единый обработчик ошибок → 400/404/500 с телом `{"detail": ...}`.

**Гейт 6 (финальный)**
- Команда: `ruff check backend/ && ruff format --check backend/`.
- Команда: открыть `/docs` — все эндпоинты, коды 200/400/404/500 задокументированы.
- Чеклист: [ ] Swagger полный [ ] docstrings везде [ ] линтер чистый [ ] нет хардкода секретов (всё из env).
- Ревью: sub-agent review-architecture — границы services/api/models, отсутствие дублирования, утечки конфигов.
