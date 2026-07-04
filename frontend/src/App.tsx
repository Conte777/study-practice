import { useState } from "react";
import UploadPage from "./pages/UploadPage";
import SearchPage from "./pages/SearchPage";

// ponytail: single-state view switch instead of a router — add react-router when routes grow.
export default function App() {
  const [tab, setTab] = useState<"upload" | "search">("upload");

  return (
    <main>
      <h1>Поиск по базе знаний</h1>
      <nav>
        <button onClick={() => setTab("upload")} disabled={tab === "upload"}>
          Загрузка
        </button>
        <button onClick={() => setTab("search")} disabled={tab === "search"}>
          Поиск
        </button>
      </nav>
      {tab === "upload" ? <UploadPage /> : <SearchPage />}
    </main>
  );
}
