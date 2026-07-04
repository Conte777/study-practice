import { useState } from "react";
import { search } from "../services/api";
import type { SearchResult } from "../types/api";

const PAGE_SIZE = 10;

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSearch = async () => {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    const res = await search(q, 0, PAGE_SIZE);
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      setResults([]);
      setTotal(null);
      return;
    }
    setResults(res.data.results);
    setTotal(res.data.total);
  };

  return (
    <section>
      <h2>Поиск</h2>
      <div className="search-bar">
        <input
          data-testid="search-input"
          placeholder="Введите запрос"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") runSearch();
          }}
        />
        <button data-testid="search-button" onClick={runSearch} disabled={loading}>
          Искать
        </button>
      </div>

      {loading && <p role="status">Загрузка результатов…</p>}
      {error && <p className="status status--error">{error}</p>}

      {!loading && total !== null && results.length === 0 && (
        <div data-testid="no-results">По вашему запросу ничего не найдено. Попробуйте изменить формулировку</div>
      )}

      <ul className="results">
        {results.map((r) => (
          <li data-testid="result-card" className="result-card" key={r.chunk_id}>
            <span data-testid="result-file-name">{r.file_name}</span>
            <span data-testid="result-page">стр. {r.page}</span>
            <p className="result-card__snippet">{r.text}</p>
            <span data-testid="result-score">{r.score.toFixed(2)}</span>
          </li>
        ))}
      </ul>

      <nav data-testid="pagination" />
    </section>
  );
}
