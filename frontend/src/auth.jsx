import { createContext, useContext, useState } from "react";
import { api, setToken } from "./api.js";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => JSON.parse(sessionStorage.getItem("user") || "null"));

  async function login(user_id, password) {
    const d = await api.post("/auth/login", { user_id, password });
    setToken(d.token);
    const u = { name: d.name, user_id: d.user_id, role: d.role };
    sessionStorage.setItem("user", JSON.stringify(u));
    setUser(u);
    return u;
  }
  function logout() {
    setToken(null); sessionStorage.removeItem("user"); setUser(null);
  }
  return <Ctx.Provider value={{ user, login, logout }}>{children}</Ctx.Provider>;
}
