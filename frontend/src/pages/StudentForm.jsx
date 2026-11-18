import { useEffect, useState } from "react";
import { useAuth } from "../auth.jsx";
import { api } from "../api.js";
import { Alert, Field } from "../ui.jsx";

const EMPTY = { father_name: "", program: "", year: "", hostel: "", dob: "", address: "", student_phone: "", parent_phone: "" };

function ImagePick({ id, label, hint, file, onFile, error }) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    if (!file) return setUrl(null);
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);
  return (
    <Field label={label} htmlFor={id} hint={hint} error={error}>
      <input id={id} type="file" accept="image/jpeg,image/png" onChange={(e) => onFile(e.target.files[0] || null)}
        className={`input file:mr-3 file:rounded file:border-0 file:bg-brand-tint file:px-3 file:py-1 file:text-sm file:font-semibold file:text-brand-dark ${error ? "input-error" : ""}`} />
      {url && <img src={url} alt={`${label} preview`} className="mt-2 max-h-40 rounded border border-line" />}
    </Field>
  );
}

export default function StudentForm() {
  const { user, logout } = useAuth();
  const [me, setMe] = useState(null);
  const [f, setF] = useState(EMPTY);
  const [photo, setPhoto] = useState(null);
  const [sign, setSign] = useState(null);
  const [agree, setAgree] = useState(false);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.get("/student/me").then(setMe).catch((e) => setError(e.message)); }, []);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  function check() {
    const e = {};
    if (f.father_name.trim().length < 2) e.father_name = "Enter the name.";
    for (const k of ["program", "year", "hostel"]) if (!f[k]) e[k] = "Select an option.";
    if (!f.dob) e.dob = "Enter your date of birth.";
    if (f.address.trim().length < 10) e.address = "Enter your full address.";
    for (const k of ["student_phone", "parent_phone"]) {
      const n = f[k].replace(/\D/g, "").length;
      if (n < 10 || n > 12) e[k] = "Enter a 10-digit mobile number.";
    }
    if (!photo) e.photo = "Upload your photograph.";
    if (!sign) e.signature = "Upload your signature.";
    return e;
  }

  async function submit(ev) {
    ev.preventDefault();
    const e = check();
    setErrors(e); setError("");
    if (Object.keys(e).length) return setError("Please correct the highlighted fields.");
    const fd = new FormData();
    Object.entries(f).forEach(([k, v]) => fd.append(k, v));
    fd.append("photo", photo); fd.append("signature", sign);
    setBusy(true);
    try {
      await api.upload("/student/submit", fd);
      setMe({ ...me, submitted: true });
    } catch (err) {
      setError(err.message); setErrors(err.fields || {});
      if (err.message.includes("already submitted")) setMe({ ...me, submitted: true });
    } finally { setBusy(false); }
  }

  const Err = (k) => errors[k];
  const cls = (k) => `input ${errors[k] ? "input-error" : ""}`;

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
          <span className="font-semibold text-brand">Hostel ID Card</span>
          <span className="flex items-center gap-3 text-sm">
            <span className="hidden text-muted sm:inline">{user.name}</span>
            <button onClick={logout} className="btn-ghost !py-1">Sign out</button>
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {!me && !error && <p className="text-sm text-muted">Loading…</p>}
        {!me && error && <Alert>{error}</Alert>}

        {me?.submitted && (
          <div className="card text-center">
            <p className="text-lg font-semibold text-brand-dark">Your ID card details have been successfully submitted.</p>
          </div>
        )}

        {me && !me.submitted && (
          <form onSubmit={submit} className="card space-y-5" noValidate>
            <div>
              <h1 className="text-lg font-bold">ID card details</h1>
              <p className="text-sm text-muted">Fill in every field carefully. You can submit only once.</p>
            </div>
            {error && <Alert>{error}</Alert>}

            <div className="grid gap-4 rounded-md bg-paper p-3 text-sm sm:grid-cols-2">
              <div><span className="text-muted">Name</span><p className="font-medium">{me.name}</p></div>
              <div><span className="text-muted">Enrollment No.</span><p className="font-medium">{me.user_id}</p></div>
            </div>

            <Field label="D/O (father's or guardian's name)" htmlFor="father_name" error={Err("father_name")}>
              <input id="father_name" className={cls("father_name")} value={f.father_name} onChange={set("father_name")} maxLength={100} />
            </Field>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="sm:col-span-2">
                <Field label="Program" htmlFor="program" error={Err("program")}>
                  <select id="program" className={cls("program")} value={f.program} onChange={set("program")}>
                    <option value="">Select program</option>
                    {me.options.programs.map((p) => <option key={p}>{p}</option>)}
                  </select>
                </Field>
              </div>
              <Field label="Year" htmlFor="year" error={Err("year")}>
                <select id="year" className={cls("year")} value={f.year} onChange={set("year")}>
                  <option value="">Select</option>
                  {me.options.years.map((y) => <option key={y}>{y}</option>)}
                </select>
              </Field>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Hostel" htmlFor="hostel" error={Err("hostel")}>
                <select id="hostel" className={cls("hostel")} value={f.hostel} onChange={set("hostel")}>
                  <option value="">Select hostel</option>
                  {me.options.hostels.map((h) => <option key={h}>{h}</option>)}
                </select>
              </Field>
              <Field label="Date of birth" htmlFor="dob" error={Err("dob")}>
                <input id="dob" type="date" className={cls("dob")} value={f.dob} onChange={set("dob")} max={new Date().toISOString().slice(0, 10)} />
              </Field>
            </div>

            <Field label="Permanent address" htmlFor="address" error={Err("address")}>
              <textarea id="address" rows={3} className={cls("address")} value={f.address} onChange={set("address")} maxLength={300} />
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Student phone" htmlFor="student_phone" error={Err("student_phone")}>
                <input id="student_phone" inputMode="tel" className={cls("student_phone")} value={f.student_phone} onChange={set("student_phone")} placeholder="10-digit mobile number" />
              </Field>
              <Field label="Parent phone" htmlFor="parent_phone" error={Err("parent_phone")}>
                <input id="parent_phone" inputMode="tel" className={cls("parent_phone")} value={f.parent_phone} onChange={set("parent_phone")} placeholder="10-digit mobile number" />
              </Field>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <ImagePick id="photo" label="Photograph" hint="Passport-size, plain background. JPG or PNG, up to 5 MB." file={photo} onFile={setPhoto} error={Err("photo")} />
              <ImagePick id="signature" label="Signature" hint="Sign on white paper and upload a clear photo. JPG or PNG, up to 5 MB." file={sign} onFile={setSign} error={Err("signature")} />
            </div>

            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-1" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
              I confirm that these details are correct. I understand they cannot be changed after submitting.
            </label>
            <button className="btn-primary w-full sm:w-auto" disabled={busy || !agree}>{busy ? "Submitting…" : "Submit details"}</button>
          </form>
        )}
      </main>
    </div>
  );
}
