import { useEffect, useState } from "react";
import "./App.css";
import UploadPage from "./pages/UploadPage";
import SearchPage from "./pages/SearchPage";
import LoginPage from "./pages/LoginPage";
import { getToken, logout } from "./services/auth";

// ponytail: single-state view switch instead of a router — add react-router when routes grow.
export default function App() {
  const [tab, setTab] = useState<"upload" | "search">("upload");
  const [token, setToken] = useState(getToken());

  // auth.ts fires "auth" on login/logout/401 — re-read the token to flip the gate.
  useEffect(() => {
    const sync = () => setToken(getToken());
    window.addEventListener("auth", sync);
    return () => window.removeEventListener("auth", sync);
  }, []);

  return (
    <main>
      <h1>Поиск по базе знаний</h1>
      {!token ? (
        <LoginPage />
      ) : (
        <>
          <nav>
            <button onClick={() => setTab("upload")} disabled={tab === "upload"}>
              Загрузка
            </button>
            <button onClick={() => setTab("search")} disabled={tab === "search"}>
              Поиск
            </button>
            <button data-testid="logout" onClick={logout}>
              Выйти
            </button>
          </nav>
          {tab === "upload" ? <UploadPage /> : <SearchPage />}
        </>
      )}
    </main>
  );
}
