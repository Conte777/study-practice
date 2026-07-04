import { expect, test } from "@playwright/test";

// QA-02 smoke: the contract selectors (CONTRACTS.md → data-testid) are present
// and carry a valid status label. Runs green against the current FE skeleton,
// so the E2E harness itself is proven wired before the full flow lands.

const STATUS_LABELS = ["Загрузка…", "Индексация…", "Готово", "Ошибка"];

test("upload view exposes the contract selectors", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("upload-dropzone")).toBeVisible();
  await expect(page.getByTestId("doc-list")).toBeVisible();

  const status = page.getByTestId("upload-status").first();
  await expect(status).toBeVisible();
  expect(STATUS_LABELS).toContain((await status.textContent())?.trim());
});

test("search view exposes the contract selectors", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Поиск" }).click();

  await expect(page.getByTestId("search-input")).toBeVisible();
  await expect(page.getByTestId("search-button")).toBeVisible();

  const card = page.getByTestId("result-card").first();
  await expect(card.getByTestId("result-file-name")).toBeVisible();
  await expect(card.getByTestId("result-page")).toBeVisible();
  await expect(card.getByTestId("result-score")).toBeVisible();
});
