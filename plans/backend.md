# План доделок: Backend (BE)

**Ветка:** `feat/be-search-history`
**Роль:** REST API, ES, парсинг, кеш.
**Директория:** `backend/`

**Что не сделано:**
- «Сохранение истории поисковых запросов» (Раздел 2, общие требования).
  Сейчас `GET /search` нигде не пишет запрос; единственная модель — `Document`.
- Авторизация по упрощённой схеме (логин/пароль, без ролей) — ТЗ допускает и «без авторизации»,
  но раз решили делать, добавляем простую.

Гейт = ① runnable-проверка ② чеклист Done ③ ревью sub-agent'ом
(`Task(subagent_type="review-code", …)`).

---

## Стадия 1 — Модель и хранение истории

**Задачи**
- `app/models/search_query.py` — SQLAlchemy-модель `SearchQuery`:
  `id: UUID`, `query: str`, `results_count: int`, `created_at: datetime` (server default `now()`).
- Экспорт в `app/models/__init__.py`; таблица создаётся в `init_db()` (уже вызывается в lifespan).
- В `app/api/search.py` после успешного ответа ES писать запись в БД.
  - Писать **до** возврата, но **не** блокировать ответ на ошибке записи: обернуть в try/except + `logger.exception`, историю считать best-effort.
  - Писать **только на промах кеша** (cache-hit не должен множить строки) — либо, наоборот, писать всегда, но тогда фиксировать `from_==0` запрос, чтобы пагинация не дублировала. Решение: писать только при `from_ == 0` (первая страница = один пользовательский запрос).
  - `results_count = total` из ES.

**Гейт 1**
- `curl "localhost:8000/api/v1/search?q=тест"` → в таблице `search_queries` появилась строка.
- Повтор того же запроса (cache-hit) → новой строки нет (или есть — по выбранному правилу, зафиксировать в чеклисте).
- Пагинация `?q=тест&from=10` → строку не пишет.
- Чеклист: [ ] модель есть [ ] таблица создаётся [ ] запись пишется на search [ ] ошибка записи не роняет ответ [ ] `from>0`/cache-hit не дублируют.

---

## Стадия 2 — Эндпоинт чтения истории

**Задачи**
- `GET /api/v1/search/history?limit=20` → последние N запросов, новейшие первыми.
- Схема ответа `SearchHistoryItem` (`query`, `results_count`, `created_at`) в `app/schemas/search.py`.
- OpenAPI-описание + пример; статусы 200/422 (bad limit).

**Гейт 2**
- `curl "localhost:8000/api/v1/search/history?limit=5"` → JSON-массив ≤5, отсортирован по `created_at desc`.
- `/docs` показывает эндпоинт.
- Чеклист: [ ] сортировка [ ] limit валидируется (`ge=1,le=100`) [ ] пустая история → `[]`.

---

## Стадия 3 — Авторизация (упрощённая, без ролей)

**Подход (лениво, без внешних зависимостей поверх нужного):**
одна таблица пользователей + JWT-токен. Регистрация опциональна — можно засидить одного demo-пользователя.

**Задачи**
- `app/models/user.py` — `User`: `id: UUID`, `username: str (unique)`, `password_hash: str`, `created_at`.
- Хеш пароля: `passlib[bcrypt]` (добавить в `pyproject.toml`). JWT: `pyjwt` (или `python-jose`), секрет из env (`JWT_SECRET`, добавить в `config.py` и `.env.example`).
- Эндпоинты в `app/api/auth.py` (router prefix `/auth`):
  - `POST /auth/register` — `{username, password}` → создать пользователя (409 если занят).
  - `POST /auth/login` — `{username, password}` → `{access_token, token_type}` (401 при неверных).
- Зависимость `get_current_user` (читает `Authorization: Bearer`, валидирует JWT, 401 при невалидном).
- Защитить `POST /documents/upload` и `GET /search` этой зависимостью (`Depends(get_current_user)`).
  `/health`, `/docs`, `/metrics` — оставить открытыми.
- Сидинг demo-пользователя при старте (env `DEMO_USER`/`DEMO_PASSWORD`) — чтобы фронт/E2E могли залогиниться.

**Гейт 3**
- `POST /auth/register` → `POST /auth/login` → получен токен.
- `GET /search` без токена → 401; с токеном → 200.
- `/docs` показывает схему авторизации (`HTTPBearer`), кнопка Authorize работает.
- Чеклист: [ ] пароль хешируется (не хранится в открытом виде) [ ] JWT-секрет из env [ ] защищены upload+search [ ] health/metrics открыты [ ] demo-user засеян.

---

## Стадия 4 — Тесты

**Задачи**
- `tests/test_search_history.py`:
  - поиск создаёт запись (мокнуть `search_chunks`, как в `test_search.py`);
  - `from>0` не пишет;
  - `GET /history` возвращает в правильном порядке;
  - ошибка записи в БД не ломает `/search` (мок сессии, кидающий на commit).
- `tests/test_auth.py`:
  - register → login → доступ к защищённому эндпоинту с токеном (200);
  - без токена / с битым токеном → 401;
  - неверный пароль → 401; повторный register → 409.
  - Обновить `conftest.py`/фикстуры: защищённые тесты шлют `Authorization` заголовок.
- Держать общее покрытие ≥ 50% (сейчас 94% — запас есть).

**Гейт 4**
- `uv run pytest -q` — зелёный.
- `uv run ruff check && uv run ruff format --check` — чисто.
- Ревью: `review-code` — гонки при записи истории, best-effort семантика, безопасность auth
  (хеширование, exp у JWT, отсутствие утечки в логах, timing-safe сравнение).
