import { useCallback, useEffect, useRef, useState } from "react";
import { search } from "../services/api";
import type { SearchResult } from "../types/api";
import { renderSnippet } from "../utils/highlight";

const PAGE_SIZE = 10;

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loadingRef = useRef(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const runSearch = async () => {
    const q = query.trim();
    if (!q || loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);
    setError(null);
    const res = await search(q, 0, PAGE_SIZE);
    loadingRef.current = false;
    setLoading(false);
    setAppliedQuery(q);
    if (!res.ok) {
      setError(res.error);
      setResults([]);
      setTotal(null);
      return;
    }
    setResults(res.data.results);
    setTotal(res.data.total);
  };

  const loadMore = useCallback(async () => {
    if (loadingRef.current || total === null || results.length >= total) return;
    loadingRef.current = true;
    setLoading(true);
    const res = await search(appliedQuery, results.length, PAGE_SIZE);
    loadingRef.current = false;
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      return;
    }
    setTotal(res.data.total);
    setResults((prev) => [...prev, ...res.data.results]);
  }, [appliedQuery, results.length, total]);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el || total === null || results.length >= total) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) loadMore();
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadMore, total, results.length]);

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
            <p className="result-card__snippet">{renderSnippet(r.text, r.highlight, appliedQuery)}</p>
            <span data-testid="result-score">{r.score.toFixed(2)}</span>
          </li>
        ))}
      </ul>

      <nav data-testid="pagination">
        {total !== null && results.length < total && <div ref={sentinelRef} className="pagination__sentinel" />}
      </nav>
    </section>
  );
}
