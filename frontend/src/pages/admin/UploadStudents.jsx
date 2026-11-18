import { useRef, useState } from "react";
import { api } from "../../api.js";
import { Alert, PageTitle } from "../../ui.jsx";
import StudentTable from "./StudentTable.jsx";

export default function UploadStudents() {
  const ref = useRef();
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [key, setKey] = useState(0);

  async function upload(e) {
    e.preventDefault();
    setBusy(true); setError(""); setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      setResult(await api.upload("/admin/students/upload", fd));
      setKey((k) => k + 1);
      setFile(null); ref.current.value = "";
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <>
      <PageTitle title="Upload Students">
        Upload an Excel file (.xlsx, .xls or .csv) with the columns <strong>Name</strong>, <strong>Enrollment No.</strong> (used as the User ID) and <strong>Password</strong>.
        An account is created for every valid row. Existing accounts are never changed.
      </PageTitle>
      <form onSubmit={upload} className="card mb-5 max-w-2xl space-y-3">
        <input ref={ref} type="file" accept=".xlsx,.xls,.csv" aria-label="Student list file" onChange={(e) => setFile(e.target.files[0] || null)}
          className="input file:mr-3 file:rounded file:border-0 file:bg-brand-tint file:px-3 file:py-1 file:text-sm file:font-semibold file:text-brand-dark" />
        <p className="text-xs text-muted">Tip: format the Enrollment No. column as Text in Excel so leading zeros are kept.</p>
        {error && <Alert>{error}</Alert>}
        <button className="btn-primary" disabled={!file || busy}>{busy ? "Creating accounts…" : "Upload and create accounts"}</button>
      </form>

      {result && (
        <div className="mb-5 max-w-3xl space-y-3">
          <Alert kind={result.imported ? "success" : "warn"}>
            {result.imported} account{result.imported === 1 ? "" : "s"} created. {result.rejected_count} row{result.rejected_count === 1 ? "" : "s"} rejected.
          </Alert>
          {result.rejected_count > 0 && (
            <div className="card !p-0 overflow-x-auto">
              <table className="w-full min-w-[480px]">
                <thead className="border-b border-line bg-paper"><tr><th className="th">Row</th><th className="th">User ID</th><th className="th">Reason</th></tr></thead>
                <tbody className="divide-y divide-line">
                  {result.rejected.map((r, i) => <tr key={i}><td className="td">{r.row}</td><td className="td">{r.user_id || "–"}</td><td className="td">{r.reason}</td></tr>)}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <h2 className="mb-2 text-base font-semibold">Student list</h2>
      <StudentTable refreshKey={key} />
    </>
  );
}
