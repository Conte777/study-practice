import { useEffect, useState, type ReactNode } from "react";
import { NavLink, Navigate, Outlet, Route, Routes } from "react-router";
import "./App.css";
import UploadPage from "./pages/UploadPage";
import SearchPage from "./pages/SearchPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import { getToken, logout } from "./services/auth";

// auth.ts fires "auth" on login/logout/401 — re-read the token to flip the gate.
function useAuthed() {
  const [token, setToken] = useState(getToken());
  useEffect(() => {
    const sync = () => setToken(getToken());
    window.addEventListener("auth", sync);
    return () => window.removeEventListener("auth", sync);
  }, []);
  return Boolean(token);
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? "navbar__link navbar__link--active" : "navbar__link";

function AppShell() {
  return (
    <>
      <header className="navbar">
        <span className="navbar__title">Поиск по базе знаний</span>
        <nav className="navbar__nav">
          <NavLink to="/upload" className={navClass}>
            Загрузка
          </NavLink>
          <NavLink to="/search" className={navClass}>
            Поиск
          </NavLink>
        </nav>
        <button data-testid="logout" className="navbar__logout" onClick={logout}>
          Выйти
        </button>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  );
}

// No token → login. Layout draws the navbar + active route.
function ProtectedLayout() {
  return useAuthed() ? <AppShell /> : <Navigate to="/login" replace />;
}

// Public auth pages: token already set → skip to /search ("auth" event
// redirects here after a successful login/register).
function AuthGate({ children }: { children: ReactNode }) {
  if (useAuthed()) return <Navigate to="/search" replace />;
  return <main className="login-view">{children}</main>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<ProtectedLayout />}>
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/search" element={<SearchPage />} />
      </Route>
      <Route path="/login" element={<AuthGate><LoginPage /></AuthGate>} />
      <Route path="/register" element={<AuthGate><RegisterPage /></AuthGate>} />
      <Route path="/" element={<Navigate to="/search" replace />} />
      <Route path="*" element={<Navigate to="/search" replace />} />
    </Routes>
  );
}
