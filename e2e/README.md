# E2E — Playwright (QA-02)

Critical path: **upload → indexing → search → display**.

## Layout

| Spec | Runs when | Purpose |
|---|---|---|
| `tests/smoke.spec.ts` | always | Login-gate contract: `data-testid`s render + a valid status label after auth. |
| `tests/critical-path.spec.ts` | `E2E_BASE_URL` set | Full QA-02 flow: upload → index → search. Runs against a live stack; skipped when the frontend is served alone (no backend). |

The FE is fully wired — auth-gate, upload with status polling, search. Both
specs authenticate first via `tests/helpers.ts`.

## Run

```bash
npm install
npx playwright install chromium

# Smoke (needs a running backend for auth):
npx playwright test

# Non-flaky gate — smoke 3× in a row:
npx playwright test smoke.spec.ts --repeat-each=3

# Full flow — stack up:
docker compose up -d --wait
E2E_BASE_URL=http://localhost:8080 npx playwright test
```

## Auth (`helpers.ts`)

`login(page, request)` registers the `e2e`/`e2e-password` demo user (ignoring a
409 if it already exists), logs in, and seeds the returned token into
`localStorage` before the app boots — so the page renders past the login gate.
API is same-origin (nginx proxies `/api/` to the backend).

Without `E2E_BASE_URL`, Playwright serves the built frontend via `vite preview`
on `:4173` (see `playwright.config.ts`). With it set, the suite reuses an
already-running stack.

## Design notes

- **No `sleep`.** Web-first assertions (`toBeVisible`, `toHaveText`) auto-wait;
  indexing is awaited via the `upload-status` → `Готово` transition.
- **Stable selectors** — `data-testid` from the FE code (`frontend/src/**`,
  mirrored in `frontend/src/types/api.ts`), never text/CSS.
- **Isolation** — fresh browser context per test. Backend data is *not* reset
  (no delete endpoint yet), so the full-flow spec targets the just-uploaded row
  via `.last()`; switch to a per-run unique filename once teardown exists.
