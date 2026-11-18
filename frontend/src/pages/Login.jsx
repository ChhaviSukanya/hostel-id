import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { Alert, Field } from "../ui.jsx";

export default function Login() {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const [uid, setUid] = useState("");
  const [pw, setPw] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const u = await login(uid.trim(), pw);
      nav(u.role === "admin" ? "/admin" : "/student", { replace: true });
    } catch (err) {
      setError(err.message); setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <p className="text-sm font-semibold text-brand">Indira Gandhi Delhi Technical University for Women</p>
          <h1 className="mt-1 text-2xl font-bold">Hostel ID Card Portal</h1>
        </div>
        <form onSubmit={submit} className="card space-y-4" noValidate>
          {error && <Alert>{error}</Alert>}
          <Field label="User ID (Enrollment No.)" htmlFor="uid">
            <input id="uid" className="input" value={uid} onChange={(e) => setUid(e.target.value)} autoComplete="username" autoFocus required />
          </Field>
          <Field label="Password" htmlFor="pw">
            <input id="pw" type="password" className="input" value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="current-password" required />
          </Field>
          <button className="btn-primary w-full" disabled={busy || !uid || !pw}>{busy ? "Signing in…" : "Sign in"}</button>
        </form>
      </div>
    </main>
  );
}
