import { defineConfig, devices } from "@playwright/test";

// Two ways to point the suite at a running UI:
//   1. Full stack:  E2E_BASE_URL=http://localhost:8080  (docker compose up)
//   2. Skeleton:    unset — Playwright serves the frontend via `vite preview`.
// The frontend skeleton makes no backend calls, so (2) needs no services.
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:4173";
const useExternal = Boolean(process.env.E2E_BASE_URL);

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  // Non-flaky is a gate requirement — no retries mask flakiness, and the
  // "3 runs in a row" check is done by `npm run test -- --repeat-each=3`.
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "on-first-retry",
    // Web-first assertions auto-wait; keep an explicit ceiling so a hung
    // backend fails fast instead of hanging the whole run.
    actionTimeout: 10_000,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: useExternal
    ? undefined
    : {
        command: "npm --prefix ../frontend run preview -- --port 4173 --strictPort",
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
