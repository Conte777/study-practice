import { useCallback, useEffect, useRef, useState } from "react";
import { getSearchHistory, search } from "../services/api";
import type { SearchHistoryItem, SearchResult } from "../types/api";
import { renderSnippet } from "../utils/highlight";

const PAGE_SIZE = 10;
const HISTORY_SIZE = 10;

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const loadingRef = useRef(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const loadHistory = useCallback(async () => {
    const res = await getSearchHistory(HISTORY_SIZE);
    if (res.ok) setHistory(res.data);
  }, []);

  const runSearch = async (raw = query) => {
    const q = raw.trim();
    if (!q || loadingRef.current) return;
    setHistoryOpen(false);
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
    loadHistory(); // refresh after a successful search
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
        <div className="search-bar__field">
          <input
            data-testid="search-input"
            placeholder="Введите запрос"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => {
              loadHistory();
              setHistoryOpen(true);
            }}
            // blur closes after the item's onMouseDown had a chance to fire
            onBlur={() => setHistoryOpen(false)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runSearch();
              if (e.key === "Escape") setHistoryOpen(false);
            }}
          />
          {historyOpen && history.length > 0 && (
            <ul data-testid="search-history" className="search-history">
              {history.map((h, i) => (
                <li
                  data-testid="search-history-item"
                  className="search-history__item"
                  key={`${h.query}-${i}`}
                  // onMouseDown, not onClick: fires before the input's onBlur closes the list
                  onMouseDown={(e) => {
                    e.preventDefault();
                    setQuery(h.query);
                    runSearch(h.query);
                  }}
                >
                  <span className="search-history__query">{h.query}</span>
                  <span className="search-history__count">{h.results_count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <button data-testid="search-button" onClick={() => runSearch()} disabled={loading}>
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
