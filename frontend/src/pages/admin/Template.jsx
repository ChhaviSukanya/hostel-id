import { useEffect, useRef, useState } from "react";
import { api } from "../../api.js";
import { Alert, AuthImage, Field, PageTitle } from "../../ui.jsx";

export default function Template() {
  const ref = useRef();
  const [s, setS] = useState(null);
  const [preview, setPreview] = useState(0);
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => api.get("/admin/card-settings").then((d) => setS({
    validity: d.validity || "", template: d.template_id ? `https://docs.google.com/presentation/d/${d.template_id}/edit` : "",
    hostels: d.hostels.join("\n"), programs: d.programs.join("\n"), has_preview: d.has_preview,
  })).catch((e) => setMsg({ kind: "error", text: e.message }));
  useEffect(() => { load(); }, []);
  if (!s) return <p className="text-sm text-muted">Loading…</p>;
  const set = (k) => (e) => setS({ ...s, [k]: e.target.value });

  async function uploadPreview() {
    const f = ref.current.files[0];
    if (!f) return;
    const fd = new FormData(); fd.append("file", f);
    try { await api.upload("/admin/template/preview", fd); setS({ ...s, has_preview: true }); setPreview((p) => p + 1); setMsg({ kind: "success", text: "Template preview updated." }); }
    catch (e) { setMsg({ kind: "error", text: e.message }); }
    ref.current.value = "";
  }

  async function save(e) {
    e.preventDefault();
    setBusy(true); setMsg(null);
    try {
      await api.put("/admin/card-settings", {
        validity: s.validity || null, template: s.template,
        hostels: s.hostels.split("\n"), programs: s.programs.split("\n"),
      });
      setMsg({ kind: "success", text: "Settings saved." }); load();
    } catch (err) { setMsg({ kind: "error", text: err.message }); }
    finally { setBusy(false); }
  }

  return (
    <>
      <PageTitle title="ID Card Template">The cards are produced from your Google Slides template. Save its link here, and upload a picture of the card to preview it.</PageTitle>
      {msg && <div className="mb-4 max-w-3xl"><Alert kind={msg.kind}>{msg.text}</Alert></div>}
      <div className="grid max-w-5xl gap-5 lg:grid-cols-2">
        <section className="card space-y-3">
          <h2 className="font-semibold">Template preview</h2>
          {s.has_preview
            ? <AuthImage key={preview} path="/admin/template/preview" alt="ID card template preview" className="w-full rounded border border-line" />
            : <p className="rounded border border-dashed border-line p-6 text-center text-sm text-muted">No template uploaded yet.</p>}
          <div className="flex flex-wrap items-center gap-2">
            <input ref={ref} type="file" accept="image/png,image/jpeg" aria-label="Template image" className="input max-w-xs text-xs" />
            <button type="button" className="btn-ghost" onClick={uploadPreview}>{s.has_preview ? "Replace preview" : "Upload preview"}</button>
          </div>
          <p className="text-xs text-muted">The current preview stays until you upload a new one.</p>
        </section>

        <form onSubmit={save} className="card space-y-4">
          <h2 className="font-semibold">Card settings</h2>
          <Field label="Google Slides template link" htmlFor="tpl" hint="The slides must contain the {{PLACEHOLDERS}} plus PHOTO and SIGNATURE boxes. Leave empty to use the template built into the script.">
            <input id="tpl" className="input" value={s.template} onChange={set("template")} placeholder="https://docs.google.com/presentation/d/…" />
          </Field>
          <Field label="Validity date (printed on every card)" htmlFor="val" hint="Required before generating.">
            <input id="val" type="date" className="input sm:max-w-[12rem]" value={s.validity} onChange={set("validity")} />
          </Field>
          <Field label="Hostel names (one per line)" htmlFor="host" hint="Shown as a dropdown on the student form.">
            <textarea id="host" rows={3} className="input" value={s.hostels} onChange={set("hostels")} />
          </Field>
          <Field label="Programs (one per line)" htmlFor="prog" hint="Shown as a dropdown. Write them exactly as they should print on the card.">
            <textarea id="prog" rows={6} className="input" value={s.programs} onChange={set("programs")} />
          </Field>
          <button className="btn-primary" disabled={busy}>{busy ? "Saving…" : "Save settings"}</button>
        </form>
      </div>
    </>
  );
}
