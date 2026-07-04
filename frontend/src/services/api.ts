import type {
  DocumentInfo,
  DocumentUploadResponse,
  SearchResponse,
} from "../types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

// Every service call resolves (never rejects) so callers never need try/catch or risk an unhandled rejection.
export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

async function request<T>(run: () => Promise<Response>): Promise<ApiResult<T>> {
  let res: Response;
  try {
    res = await run();
  } catch {
    return { ok: false, error: "Нет соединения с сервером" };
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { detail?: string };
    return { ok: false, error: body.detail ?? `HTTP ${res.status}` };
  }
  return { ok: true, data: (await res.json()) as T };
}

export function uploadDocument(file: File): Promise<ApiResult<DocumentUploadResponse>> {
  const form = new FormData();
  form.append("file", file);
  return request(() => fetch(`${BASE_URL}/documents/upload`, { method: "POST", body: form }));
}

export function listDocuments(): Promise<ApiResult<DocumentInfo[]>> {
  return request(() => fetch(`${BASE_URL}/documents`));
}

export function search(q: string, from = 0, size = 10): Promise<ApiResult<SearchResponse>> {
  const params = new URLSearchParams({ q, from: String(from), size: String(size) });
  return request(() => fetch(`${BASE_URL}/search?${params}`));
}
