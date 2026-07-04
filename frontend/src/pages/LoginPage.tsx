import { useState } from "react";
import { login, register } from "../services/auth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (action: typeof login) => {
    if (!username || !password || busy) return;
    setBusy(true);
    setError(null);
    const res = await action(username, password);
    setBusy(false);
    if (!res.ok) setError(res.error); // success re-renders App via the "auth" event
  };

  return (
    <section className="login">
      <h2>Вход</h2>
      <form
        className="login__form"
        onSubmit={(e) => {
          e.preventDefault();
          submit(login);
        }}
      >
        <input
          data-testid="login-username"
          placeholder="Имя пользователя"
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          data-testid="login-password"
          type="password"
          placeholder="Пароль"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="status status--error">{error}</p>}
        <div className="login__actions">
          <button data-testid="login-submit" type="submit" disabled={busy}>
            Войти
          </button>
          <button
            data-testid="register-submit"
            type="button"
            onClick={() => submit(register)}
            disabled={busy}
          >
            Регистрация
          </button>
        </div>
      </form>
    </section>
  );
}
