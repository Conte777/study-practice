# План: DevOps (DO)

**Роль:** контейнеризация, docker-compose, CI/CD, мониторинг, окружение.
**Стек:** Docker / Docker Compose, Nginx, GitHub Actions, Prometheus, Grafana.
**Файлы:** `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml`, `init.sh`, `README.md`.

Стадии по фичам. Гейт = ① runnable-проверка ② чеклист Done (ID ТЗ) ③ ревью sub-agent'ом.

Ревью гейта:
> Task(subagent_type="review-code", prompt="Проверь стадию N плана devops: соответствие <ID>, отсутствие секретов в образах, healthchecks, порядок старта зависимостей. Верни confirmed-findings.")

---

## Стадия 1 — Dockerfile backend (DO-01)

**Задачи**
- Multi-stage Dockerfile (Python 3.12-slim), установка из `requirements.txt`, запуск uvicorn.
- Non-root user, кеш слоёв зависимостей.

**Гейт 1**
- Команда: `docker build -t app ./backend` → успешно.
- Команда: `docker run --rm -p8000:8000 app` → `/docs` отвечает.
- Чеклист: [ ] DO-01 образ собирается [ ] запускается [ ] non-root [ ] нет секретов в слоях.
- Ревью: sub-agent review-code — размер образа, кеширование слоёв, отсутствие dev-зависимостей в рантайме.

---

## Стадия 2 — Dockerfile frontend + Nginx (DO-02)

**Задачи**
- Multi-stage: `node build` → отдача статики через `nginx:alpine`.
- Nginx: gzip, проксирование `/api` на backend, SPA-fallback на `index.html`.

**Гейт 2**
- Команда: `docker build -t front ./frontend && docker run --rm -p8080:80 front` → страница отдаётся.
- Чеклист: [ ] DO-02 сборка+Nginx [ ] статика отдаётся [ ] /api проксируется [ ] SPA-роуты не 404.
- Ревью: sub-agent review-code — конфиг Nginx (кеш-хедеры, проксирование), отсутствие source-map в проде.

---

## Стадия 3 — docker-compose + окружение (DO-03, DO-04)

**Задачи**
- `docker-compose.yml`: `app`, `front`, `postgres`, `elasticsearch`, `redis`.
- `depends_on` + healthchecks (ES/PG готовы раньше app).
- Все секреты через env; `.env.example` в репо, `.env` в `.gitignore`.

**Гейт 3**
- Команда: `docker compose up -d` **одной командой** → все сервисы `healthy`.
- Команда: сквозной сценарий (загрузка→поиск) работает через поднятый стек.
- Чеклист: [ ] DO-03 5 сервисов [ ] DO-04 секреты в env, .env.example есть [ ] стартует одной командой [ ] healthchecks.
- Ревью: sub-agent review-security — нет паролей в compose/образах; сети/порты не торчат лишнего наружу.

---

## Стадия 4 — CI/CD GitHub Actions (DO-05)

**Задачи**
- `.github/workflows/ci.yml`: на push в `main` — линтеры (ruff, eslint) + базовые тесты (pytest).
- При успехе — сборка образов (`docker build` backend+frontend).

**Гейт 4**
- Команда: пуш в ветку → workflow зелёный; лог показывает линт+тесты+build.
- Кейс: намеренно сломать линт → workflow красный (гейт реально блокирует).
- Чеклист: [ ] DO-05 линтеры [ ] тесты [ ] сборка образов при успехе [ ] падает на ошибке.
- Ревью: sub-agent review-code — кеш зависимостей в CI, отсутствие секретов в логах, matrix при необходимости.

---

## Стадия 5 — Мониторинг Prometheus + Grafana (DO-06)

**Задачи**
- Backend отдаёт метрики (`/metrics`): счётчик запросов к `/search`, среднее время ответа.
- Prometheus + Grafana в compose; дашборд с этими метриками.

**Гейт 5**
- Команда: `curl localhost:8000/metrics` → метрики есть; Grafana-дашборд рисует RPS и latency `/search`.
- Чеклист: [ ] DO-06 Prometheus собирает [ ] Grafana-дашборд [ ] метрики /search присутствуют.
- Ревью: sub-agent review-code — корректность лейблов метрик, отсутствие high-cardinality, provisioning дашборда как код.

---

## Стадия 6 — init.sh + README (DO-07, критерий «Документация»)

**Задачи**
- `init.sh`: скачивает 10 тестовых PDF-лекций из открытого доступа, грузит через `/api/v1/documents/upload`.
- `README.md`: запуск одной командой, переменные окружения, архитектура.

**Гейт 6 (финальный)**
- Команда: чистое окружение → `docker compose up -d && ./init.sh` → 10 документов проиндексированы, поиск находит.
- Чеклист: [ ] DO-07 init.sh качает+грузит 10 файлов [ ] README покрывает запуск+env [ ] «up одной командой» воспроизводится с нуля.
- Ревью: sub-agent review-code — идемпотентность init.sh, обработка ошибок скачивания/загрузки, ретраи на неготовый API.
