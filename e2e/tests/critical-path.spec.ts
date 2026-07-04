import path from "node:path";

import { expect, test } from "@playwright/test";

import { login } from "./helpers";

// QA-02 critical path: upload → indexing → search → display.
//
// Gated behind E2E_FULL_FLOW=1 because it needs the *wired* frontend
// (FE-02/03/04/07: real upload input, status polling, search fetch, highlight
// render) AND the full stack up (docker compose: app + postgres + ES + redis).
// The current FE is a static skeleton, so this stays off by default; the smoke
// suite proves the harness meanwhile. Flip the env var once FE is wired.
const FULL_FLOW = process.env.E2E_FULL_FLOW === "1";

const OK_PDF = path.resolve(__dirname, "../../tests/fixtures/ok.pdf");

test.describe("critical path", () => {
  test.skip(!FULL_FLOW, "needs wired FE + full stack (set E2E_FULL_FLOW=1)");

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
