import type { ApiResult } from "./api";
import type { TokenResponse } from "../types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "token";

// "auth" fires on any token change so App re-renders the login gate.
const notify = () => window.dispatchEvent(new Event("auth"));

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  notify();
}

export const logout = clearToken;

async function auth(path: "login" | "register", username: string, password: string): Promise<ApiResult<void>> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/auth/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
  } catch {
    return { ok: false, error: "Нет соединения с сервером" };
  }
  const body = (await res.json().catch(() => ({}))) as Partial<TokenResponse> & { detail?: string };
  if (!res.ok || !body.access_token) {
    return { ok: false, error: body.detail ?? `HTTP ${res.status}` };
  }
  localStorage.setItem(TOKEN_KEY, body.access_token);
  notify();
  return { ok: true, data: undefined };
}

export const login = (username: string, password: string) => auth("login", username, password);
export const register = (username: string, password: string) => auth("register", username, password);
