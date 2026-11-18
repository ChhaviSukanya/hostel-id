import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { Alert, AuthImage, Badge, PageTitle } from "../../ui.jsx";
import StudentTable from "./StudentTable.jsx";

function Stat({ label, value }) {
  return (
    <div className="card">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-3xl font-bold">{value ?? "–"}</p>
    </div>
  );
}

function Detail({ userId, onClose, onChanged }) {
  const [d, setD] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.get(`/admin/students/${encodeURIComponent(userId)}`).then(setD).catch((e) => setError(e.message)); }, [userId]);

  async function reset() {
    if (!window.confirm("Remove this submission so the student can fill the form again? Their photo and signature will be deleted.")) return;
    try { await api.del(`/admin/students/${encodeURIComponent(userId)}/submission`); onChanged(); onClose(); }
    catch (e) { setError(e.message); }
  }
  const img = (k) => `/admin/students/${encodeURIComponent(userId)}/image/${k}`;

  return (
    <div className="fixed inset-0 z-20 flex justify-end bg-ink/40" onClick={onClose}>
      <aside className="h-full w-full max-w-md overflow-y-auto bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Student details">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold">{d?.name || "Student"}</h2>
            <p className="text-sm text-muted">{userId}</p>
          </div>
          <button className="btn-ghost !py-1" onClick={onClose}>Close</button>
        </div>
        {error && <Alert>{error}</Alert>}
        {d && <div className="mb-3"><Badge submitted={d.submitted} /></div>}
        {d && !d.submitted && <p className="text-sm text-muted">This student has not submitted the form yet.</p>}
        {d?.details && (
          <>
            <div className="mb-4 flex gap-3">
              <figure><AuthImage path={img("photo")} alt="Photograph" className="h-40 w-32 rounded border border-line object-cover" /><figcaption className="mt-1 text-xs text-muted">Photograph</figcaption></figure>
              <figure><AuthImage path={img("signature")} alt="Signature" className="h-20 w-40 rounded border border-line object-contain" /><figcaption className="mt-1 text-xs text-muted">Signature</figcaption></figure>
            </div>
            <dl className="divide-y divide-line text-sm">
              {Object.entries(d.details).map(([k, v]) => (
                <div key={k} className="grid grid-cols-3 gap-2 py-2"><dt className="text-muted">{k}</dt><dd className="col-span-2 break-words">{v}</dd></div>
              ))}
            </dl>
            <button className="btn-danger mt-5" onClick={reset}>Reset submission</button>
          </>
        )}
      </aside>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState({});
  const [open, setOpen] = useState(null);
  const [key, setKey] = useState(0);
  useEffect(() => { api.get("/admin/stats").then(setStats).catch(() => {}); }, [key]);
  return (
    <>
      <PageTitle title="Dashboard">Submission progress and the list of all students. Select a student to see their details.</PageTitle>
      <div className="mb-5 grid gap-3 sm:grid-cols-3">
        <Stat label="Total students" value={stats.total} />
        <Stat label="Submitted" value={stats.submitted} />
        <Stat label="Not submitted" value={stats.pending} />
      </div>
      <StudentTable onOpen={setOpen} refreshKey={key} />
      {open && <Detail userId={open} onClose={() => setOpen(null)} onChanged={() => setKey((k) => k + 1)} />}
    </>
  );
}
