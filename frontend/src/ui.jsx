import { useEffect, useState } from "react";
import { api } from "./api.js";

export function Alert({ kind = "error", children }) {
  const styles = {
    error: "border-bad bg-bad-tint text-bad",
    success: "border-brand bg-brand-tint text-brand-dark",
    warn: "border-warn bg-warn-tint text-warn",
  };
  return (
    <div role={kind === "error" ? "alert" : "status"} className={`rounded-md border px-4 py-3 text-sm ${styles[kind]}`}>
      {children}
    </div>
  );
}

export function Field({ label, error, hint, htmlFor, children }) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1 block text-sm font-medium">{label}</label>
      {children}
      {hint && !error && <p className="mt-1 text-xs text-muted">{hint}</p>}
      {error && <p className="mt-1 text-xs text-bad">{error}</p>}
    </div>
  );
}

export function Badge({ submitted }) {
  return submitted ? (
    <span className="rounded-full bg-brand-tint px-2.5 py-0.5 text-xs font-semibold text-brand-dark">Submitted</span>
  ) : (
    <span className="rounded-full bg-warn-tint px-2.5 py-0.5 text-xs font-semibold text-warn">Pending</span>
  );
}

// Loads an image through the authenticated API (an <img src> cannot send the login token).
export function AuthImage({ path, alt, className }) {
  const [src, setSrc] = useState(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let url, live = true;
    setSrc(null); setFailed(false);
    api.blobUrl(path).then((u) => { url = u; live ? setSrc(u) : URL.revokeObjectURL(u); }).catch(() => live && setFailed(true));
    return () => { live = false; url && URL.revokeObjectURL(url); };
  }, [path]);
  if (failed) return <div className={`flex items-center justify-center bg-paper text-xs text-muted ${className}`}>No image</div>;
  return src ? <img src={src} alt={alt} className={className} /> : <div className={`animate-pulse bg-paper ${className}`} />;
}

export function PageTitle({ title, children }) {
  return (
    <div className="mb-5">
      <h1 className="text-xl font-bold">{title}</h1>
      {children && <p className="mt-1 max-w-2xl text-sm text-muted">{children}</p>}
    </div>
  );
}
