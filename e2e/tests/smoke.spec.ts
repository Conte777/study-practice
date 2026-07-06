import { expect, test } from "@playwright/test";

// QA-02 smoke: the FE is now auth-gated, so with no backend the only thing that
// renders is the login screen. Assert its contract selectors — this proves the
// E2E harness is wired without needing the full stack. The logged-in upload/
// search selectors are covered by critical-path.spec.ts (needs E2E_BASE_URL).

test("login gate exposes its contract selectors", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("login-username")).toBeVisible();
  await expect(page.getByTestId("login-password")).toBeVisible();
  await expect(page.getByTestId("login-submit")).toBeVisible();
});

test("register page exposes its contract selectors", async ({ page }) => {
  await page.goto("/register");
  await expect(page.getByTestId("register-username")).toBeVisible();
  await expect(page.getByTestId("register-password")).toBeVisible();
  await expect(page.getByTestId("register-submit")).toBeVisible();
});
