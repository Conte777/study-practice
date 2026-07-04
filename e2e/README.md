# E2E — Playwright (QA-02)

Critical path: **upload → indexing → search → display**.

## Layout

| Spec | Runs when | Purpose |
|---|---|---|
| `tests/smoke.spec.ts` | always | Contract `data-testid`s render + a valid status label. Proves the harness against the current FE skeleton. |
| `tests/critical-path.spec.ts` | `E2E_FULL_FLOW=1` | Full QA-02 flow. Needs the **wired** FE (FE-02/03/04/07) + full stack. Skipped by default. |

## Run

```bash
npm install
npx playwright install chromium

# Skeleton (no backend needed — FE makes no API calls yet):
npx playwright test

# Non-flaky gate — smoke 3× in a row:
npx playwright test smoke.spec.ts --repeat-each=3

# Full flow once FE is wired + stack is up:
docker compose up -d --wait
E2E_BASE_URL=http://localhost:8080 E2E_FULL_FLOW=1 npx playwright test
```

Without `E2E_BASE_URL`, Playwright serves the built frontend via `vite preview`
on `:4173` (see `playwright.config.ts`). With it set, the suite reuses an
already-running stack.

## Design notes

- **No `sleep`.** Web-first assertions (`toBeVisible`, `toHaveText`) auto-wait;
  indexing is awaited via the `upload-status` → `Готово` transition.
- **Stable selectors** — `data-testid` from `CONTRACTS.md`, never text/CSS.
- **Isolation** — fresh browser context per test. Backend data is *not* reset
  (no delete endpoint yet), so the full-flow spec targets the just-uploaded row
  via `.last()`; switch to a per-run unique filename once teardown exists.
