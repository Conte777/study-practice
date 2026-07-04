import path from "node:path";

import { expect, test } from "@playwright/test";

import { login } from "./helpers";

// QA-02 critical path: upload → indexing → search → display.
//
// Needs the full stack (docker compose: app + postgres + ES + redis) — the FE
// is now fully wired, so the only prerequisite is a live backend. Runs whenever
// E2E_BASE_URL points at it; skips when the suite serves the frontend alone via
// `vite preview` (no backend), where the smoke suite proves the harness.
const FULL_STACK = Boolean(process.env.E2E_BASE_URL);

const OK_PDF = path.resolve(__dirname, "../../tests/fixtures/ok.pdf");

test.describe("critical path", () => {
  test.skip(!FULL_STACK, "needs the full stack — set E2E_BASE_URL (docker compose up)");

  test("upload a document, wait for indexed, then find it in search", async ({ page, request }) => {
    await login(page, request);
    await page.goto("/");

    // --- Upload ---
    // Robust to either a native <input type=file> or a dropzone that reveals one.
    const chooser = page.waitForEvent("filechooser");
    await page.getByTestId("upload-dropzone").click();
    await (await chooser).setFiles(OK_PDF);

    // .last(): a persistent stack (no delete endpoint) accumulates prior ok.pdf
    // rows across runs — target the just-uploaded one to avoid strict-mode
    // violations. Swap for a per-run unique filename if ordering isn't newest-last.
    const item = page.getByTestId("upload-item").filter({ hasText: "ok.pdf" }).last();
    await expect(item).toBeVisible();

    // --- Indexing: wait for "Готово" (indexed), not a fixed sleep ---
    await expect(item.getByTestId("upload-status")).toHaveText("Готово", {
      timeout: 30_000,
    });

    // --- Search ---
    await page.getByRole("button", { name: "Поиск" }).click();
    await page.getByTestId("search-input").fill("knowledge base");
    await page.getByTestId("search-button").click();

    // --- Display: card fields + highlight ---
    const card = page.getByTestId("result-card").first();
    await expect(card).toBeVisible();
    await expect(card.getByTestId("result-file-name")).toHaveText(/ok\.pdf/);
    await expect(card.getByTestId("result-page")).toBeVisible();
    await expect(card.getByTestId("result-score")).toBeVisible();
    // Highlight contract: matched term wrapped in <mark> (sanitized on FE).
    // .first(): a multi-word query yields one <mark> per term, so scope to one.
    await expect(card.locator("mark").first()).toBeVisible();
  });
});
