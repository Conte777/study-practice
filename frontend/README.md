# Frontend — UI поиска по базе знаний

React 19 + TypeScript + Vite. Линтер — **oxlint** (не ESLint). Dev-порт **8080**.

## Скрипты

| Команда | Что делает |
|---|---|
| `npm run dev` | dev-сервер на `:8080` |
| `npm run lint` | oxlint |
| `npm run build` | `tsc -b && vite build` — type-check входит в сборку |

## Структура `src/`

| Путь | Назначение |
|---|---|
| `App.tsx` | корень: auth-gate + переключение вкладок Загрузка/Поиск |
| `pages/` | `LoginPage`, `UploadPage`, `SearchPage` |
| `services/` | `api.ts` (fetch-обёртки), `auth.ts` (токен, событие `auth`) |
| `types/api.ts` | ручное зеркало Pydantic-схем бэкенда (guard — `test_contract.py`) |
| `utils/` | `highlight.tsx` — рендер `<mark>`-подсветки |

## Окружение

`VITE_API_BASE_URL` запекается на билд-тайме (в docker — через build-arg
compose). В проде nginx проксирует `/api/` → `app:8000`, поэтому фронт и API
same-origin.
