let token = sessionStorage.getItem("token");
export const setToken = (t) => {
  token = t;
  t ? sessionStorage.setItem("token", t) : sessionStorage.removeItem("token");
};

export class ApiError extends Error {
  constructor(message, fields) { super(message); this.fields = fields || {}; }
}

async function request(path, { json, body, method = "GET", raw = false } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (json) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  const res = await fetch(`/api${path}`, { method, headers, body });
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/auth")) {
      setToken(null); sessionStorage.removeItem("user"); window.location.href = "/login";
    }
    let message = "Something went wrong. Please try again.", fields;
    try {
      const d = (await res.json()).detail;
      if (typeof d === "string") message = d;
      else if (d?.errors) { message = "Please correct the highlighted fields."; fields = d.errors; }
      else if (Array.isArray(d)) message = d.map((x) => x.msg).join(" ");
    } catch { /* keep default */ }
    throw new ApiError(message, fields);
  }
  return raw ? res : res.json();
}

export const api = {
  get: (p) => request(p),
  post: (p, json) => request(p, { method: "POST", json }),
  put: (p, json) => request(p, { method: "PUT", json }),
  del: (p) => request(p, { method: "DELETE" }),
  upload: (p, formData) => request(p, { method: "POST", body: formData }),
  async blobUrl(p) { return URL.createObjectURL(await (await request(p, { raw: true })).blob()); },
  async download(p, filename) {
    const url = await api.blobUrl(p);
    const a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  },
};
