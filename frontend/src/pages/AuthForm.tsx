import { useState } from "react";
import { Link } from "react-router";
import { login, register } from "../services/auth";

interface Props {
  mode: "login" | "register";
}

const COPY = {
  login: {
    title: "Вход",
    submit: "Войти",
    action: login,
    hint: "Нет аккаунта?",
    linkText: "Зарегистрироваться",
    linkTo: "/register",
  },
  register: {
    title: "Регистрация",
    submit: "Зарегистрироваться",
    action: register,
    hint: "Уже есть аккаунт?",
    linkText: "Войти",
    linkTo: "/login",
  },
} as const;

export default function AuthForm({ mode }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const c = COPY[mode];

  const submit = async () => {
    if (busy) return;
    if (!username || !password) {
      setError("Введите имя пользователя и пароль");
      return;
    }
    setBusy(true);
    setError(null);
    const res = await c.action(username, password);
    setBusy(false);
    if (!res.ok) setError(res.error); // success re-renders App via the "auth" event
  };

  return (
    <section className="login">
      <h2>{c.title}</h2>
      <form
        className="login__form"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <input
          data-testid={`${mode}-username`}
          placeholder="Имя пользователя"
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          data-testid={`${mode}-password`}
          type="password"
          placeholder="Пароль"
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="status status--error">{error}</p>}
        <button data-testid={`${mode}-submit`} type="submit" disabled={busy}>
          {c.submit}
        </button>
      </form>
      <p className="login__switch">
        {c.hint} <Link to={c.linkTo}>{c.linkText}</Link>
      </p>
    </section>
  );
}
