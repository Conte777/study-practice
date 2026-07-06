// Manual mirror of backend/app/schemas (Pydantic = source of truth).
// ponytail: hand-written mirror; generate from openapi.json via openapi-typescript if schemas drift.

export type DocumentStatus = "uploaded" | "indexing" | "indexed" | "error";

// FE-02 labels per status.
export const STATUS_LABELS: Record<DocumentStatus, string> = {
  uploaded: "Загрузка…",
  indexing: "Индексация…",
  indexed: "Готово",
  error: "Ошибка",
};

export interface ErrorResponse {
  detail: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Credentials {
  username: string;
  password: string;
}

export interface SearchHistoryItem {
  query: string;
  results_count: number;
  created_at: string; // ISO datetime
}

export interface DocumentInfo {
  id: string; // UUID
  file_name: string;
  status: DocumentStatus;
  uploaded_at: string; // ISO datetime
}

export type DocumentUploadResponse = DocumentInfo;

export interface SearchResult {
  chunk_id: string;
  file_name: string;
  page: number;
  text: string;
  score: number;
  highlight: string | null; // <mark>…</mark>; null → fall back to `text`
}

export interface SearchResponse {
  total: number;
  results: SearchResult[];
}
