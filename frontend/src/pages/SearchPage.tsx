// Skeleton — FE-04/06/07 stage fills logic (query, highlight render, pagination).
export default function SearchPage() {
  return (
    <section>
      <h2>Поиск</h2>
      <input data-testid="search-input" placeholder="Введите запрос" />
      <button data-testid="search-button">Искать</button>

      <div data-testid="result-card">
        <span data-testid="result-file-name">ok.pdf</span>
        <span data-testid="result-page">стр. 1</span>
        <span data-testid="result-score">1.42</span>
      </div>

      <div data-testid="no-results" hidden>
        Ничего не найдено
      </div>
      <nav data-testid="pagination" />
    </section>
  );
}
