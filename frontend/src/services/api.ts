import type {
  DocumentInfo,
  DocumentUploadResponse,
  SearchResponse,
} from "../types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return json(await fetch(`${BASE_URL}/documents/upload`, { method: "POST", body: form }));
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  return json(await fetch(`${BASE_URL}/documents`));
}

export async function search(q: string, from = 0, size = 10): Promise<SearchResponse> {
  const params = new URLSearchParams({ q, from: String(from), size: String(size) });
  return json(await fetch(`${BASE_URL}/search?${params}`));
}
