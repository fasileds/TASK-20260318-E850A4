import { useState } from "react";
import { api, setAuthToken, setUsernameHeader } from "../api";

export function LoginPanel({ onLoggedIn }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleLogin(e) {
    e.preventDefault();
    setError("");
    try {
      const { data } = await api.post("/auth/login", { username, password });
      setAuthToken(data.token);
      setUsernameHeader(data.user.username);
      onLoggedIn(data.user);
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    }
  }

  return (
    <section className="panel">
      <h2>Username/Password Login</h2>
      <form className="grid" onSubmit={handleLogin}>
        <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" required />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" required />
        <button type="submit">Login</button>
      </form>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
