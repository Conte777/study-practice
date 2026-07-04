# Поиск по базе знаний университета

Каркас-основа: межкомандные контракты зафиксированы в коде (Pydantic → OpenAPI, TS-зеркало,
compose-окружение). Мок-BE запускается с первого дня — FE/QA кодят против живых схем.
Фичи наполняются по стадиям в `plans/{backend,frontend,devops,qa}.md`.

**Контракты — в [`CONTRACTS.md`](./CONTRACTS.md)** (единая точка для всех ролей).

## Стек

- Backend: FastAPI + Pydantic (uv), `/docs` авто-Swagger.
- Frontend: React + TypeScript (Vite, strict).
- Инфра: docker-compose — `app, front, postgres, elasticsearch, redis`.

## Быстрый старт

```bash
./init.sh                 # .env + зависимости BE/FE
# BE:  cd backend && uv run uvicorn app.main:app --reload   → http://localhost:8000/docs
# FE:  cd frontend && npm run dev                            → http://localhost:8080
# всё: docker compose up --build
```

## Структура

```
backend/app/{api,core,models,schemas,services}/  main.py   # schemas/ = источник правды контракта
frontend/src/{components,pages,services,types}/  App.tsx    # types/api.ts = зеркало схем
docker-compose.yml  .env.example  CONTRACTS.md  init.sh
tests/fixtures/     .github/workflows/ci.yml
```
