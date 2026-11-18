import { useCallback, useEffect, useState } from "react";
import { api } from "../../api.js";
import { Alert, PageTitle } from "../../ui.jsx";

const Check = ({ ok, children }) => (
  <li className="flex items-start gap-2 text-sm">
    <span aria-hidden className={`mt-0.5 inline-block h-4 w-4 shrink-0 rounded-full text-center text-[10px] leading-4 text-white ${ok ? "bg-brand" : "bg-line"}`}>{ok ? "✓" : ""}</span>
    <span className={ok ? "" : "text-muted"}>{children}<span className="sr-only">{ok ? " (done)" : " (not done)"}</span></span>
  </li>
);

export default function Generation() {
  const [sum, setSum] = useState(null);
  const [run, setRun] = useState(undefined);
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState("");

  const refresh = useCallback(() => {
    api.get("/admin/generation/summary").then(setSum).catch((e) => setMsg(e.message));
    return api.get("/admin/generation/latest").then(setRun).catch(() => setRun(null));
  }, []);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (run?.status !== "running") return;
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [run?.status, refresh]);

  async function excel() {
    setBusy("excel"); setMsg(null);
    try { await api.download("/admin/generation/excel", `hostel_id_cards_${new Date().toISOString().slice(0, 10)}.xlsx`); }
    catch (e) { setMsg(e.message); } finally { setBusy(""); }
  }
  async function generate() {
    if (!window.confirm(`Generate ID cards for ${sum.submitted} student(s)? This can take several minutes.`)) return;
    setBusy("run"); setMsg(null);
    try { await api.post("/admin/generation/run"); await refresh(); } catch (e) { setMsg(e.message); } finally { setBusy(""); }
  }

  if (!sum) return <p className="text-sm text-muted">Loading…</p>;
  const ready = sum.submitted > 0 && sum.validity_set && sum.drive_ready;
  const running = run?.status === "running";
  const pct = run?.total ? Math.round((run.done / run.total) * 100) : 0;

  return (
    <>
      <PageTitle title="Excel & ID Generation">
        Compile the submitted details into the Excel sheet your script expects, then generate the ID cards with your Google Apps Script.
      </PageTitle>
      {msg && <div className="mb-4 max-w-3xl"><Alert>{msg}</Alert></div>}

      <div className="grid max-w-5xl gap-5 lg:grid-cols-2">
        <section className="card space-y-3">
          <h2 className="font-semibold">Before you start</h2>
          <ul className="space-y-2">
            <Check ok={sum.submitted > 0}>{sum.submitted} student{sum.submitted === 1 ? "" : "s"} submitted</Check>
            <Check ok={sum.validity_set}>Validity date set (ID Card Template page)</Check>
            <Check ok={sum.drive_ready}>Google Drive connected (photos and signatures)</Check>
            <Check ok={sum.script_ready}>Apps Script connected (automatic generation)</Check>
            <Check ok={sum.template_set}>Template link saved (optional, otherwise the script’s default is used)</Check>
          </ul>
        </section>

        <section className="card space-y-3">
          <h2 className="font-semibold">Step 1: Excel file</h2>
          <p className="text-sm text-muted">Columns, order and photo/signature links match your existing sheet. Photos are uploaded to Drive first, so the first export can take a moment.</p>
          <button className="btn-ghost" onClick={excel} disabled={!ready || !!busy}>{busy === "excel" ? "Preparing…" : "Download Excel"}</button>
        </section>

        <section className="card space-y-3 lg:col-span-2">
          <h2 className="font-semibold">Step 2: Generate ID cards</h2>
          <p className="text-sm text-muted">Runs your Apps Script on all submitted students and produces one PDF (front and back for every student).</p>
          <button className="btn-primary" onClick={generate} disabled={!ready || !sum.script_ready || running || !!busy}>
            {running ? "Generating…" : "Generate ID cards"}
          </button>

          {run && (
            <div className="space-y-3 border-t border-line pt-3">
              <p className="text-sm"><span className="font-medium">Latest run:</span> {run.status === "running" ? run.stage : run.status === "done" ? "Finished" : "Failed"}</p>
              {running && (
                <div role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} className="h-2 w-full overflow-hidden rounded bg-paper">
                  <div className="h-full bg-brand transition-all" style={{ width: `${pct}%` }} />
                </div>
              )}
              {run.status === "failed" && <Alert>{run.message}</Alert>}
              {run.status === "done" && (
                <div className="flex flex-wrap gap-2">
                  {run.has_pdf && <button className="btn-primary" onClick={() => api.download(`/admin/generation/runs/${run.id}/pdf`, "hostel_id_cards.pdf")}>Download ID cards (PDF)</button>}
                  {run.slides_url && <a className="btn-ghost" href={run.slides_url} target="_blank" rel="noreferrer">Open in Google Slides</a>}
                </div>
              )}
              {run.warnings.length > 0 && (
                <Alert kind="warn">
                  <p className="mb-1 font-semibold">{run.warnings.length} item(s) need attention:</p>
                  <ul className="max-h-48 list-disc space-y-0.5 overflow-y-auto pl-5">{run.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
                </Alert>
              )}
            </div>
          )}
        </section>
      </div>
    </>
  );
}
