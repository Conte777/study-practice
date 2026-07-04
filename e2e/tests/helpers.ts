import type { APIRequestContext, Page } from "@playwright/test";

// Demo user for the auth-gated FE. Register is idempotent-ish: 409 (already
// exists) is fine, we just log in afterwards. API is same-origin as the FE
// (nginx proxies /api/ to the backend), so request's baseURL resolves it.
const CREDS = { username: "e2e", password: "e2e-password" };

export async function login(page: Page, request: APIRequestContext): Promise<void> {
  await request.post("/api/v1/auth/register", { data: CREDS }).catch(() => undefined);
  const res = await request.post("/api/v1/auth/login", { data: CREDS });
  const { access_token } = (await res.json()) as { access_token: string };
  // Seed the token before the app boots so it renders past the login gate.
  await page.addInitScript((token) => localStorage.setItem("token", token), access_token);
}
