import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { Badge } from "../../ui.jsx";

export default function StudentTable({ onOpen, refreshKey = 0 }) {
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0, page_size: 25 });
  const [error, setError] = useState("");

  useEffect(() => { const t = setTimeout(() => { setQ(search); setPage(1); }, 300); return () => clearTimeout(t); }, [search]);
  useEffect(() => {
    const p = new URLSearchParams({ search: q, status, page });
    api.get(`/admin/students?${p}`).then((d) => { setData(d); setError(""); }).catch((e) => setError(e.message));
  }, [q, status, page, refreshKey]);

  const pages = Math.max(1, Math.ceil(data.total / data.page_size));
  return (
    <div className="card !p-0">
      <div className="flex flex-col gap-2 border-b border-line p-3 sm:flex-row">
        <input className="input sm:max-w-xs" placeholder="Search by name or enrollment no." aria-label="Search students" value={search} onChange={(e) => setSearch(e.target.value)} />
        <select className="input sm:w-40" aria-label="Filter by status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="all">All students</option>
          <option value="submitted">Submitted</option>
          <option value="pending">Pending</option>
        </select>
      </div>
      {error && <p className="p-3 text-sm text-bad">{error}</p>}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px]">
          <thead className="border-b border-line bg-paper"><tr>
            <th className="th">Student name</th><th className="th">User ID / Enrollment No.</th><th className="th">Status</th>
          </tr></thead>
          <tbody className="divide-y divide-line">
            {data.items.map((s) => (
              <tr key={s.user_id} className={onOpen ? "cursor-pointer hover:bg-paper" : ""} onClick={() => onOpen?.(s.user_id)}>
                <td className="td font-medium">
                  {onOpen ? <button className="text-left hover:underline">{s.name}</button> : s.name}
                </td>
                <td className="td">{s.user_id}</td>
                <td className="td"><Badge submitted={s.submitted} /></td>
              </tr>
            ))}
            {!data.items.length && <tr><td colSpan={3} className="td text-center text-muted">No students found.</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-line p-3 text-sm">
        <span className="text-muted">{data.total} student{data.total === 1 ? "" : "s"}</span>
        <span className="flex items-center gap-2">
          <button className="btn-ghost !py-1" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
          <span>Page {page} of {pages}</span>
          <button className="btn-ghost !py-1" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
        </span>
      </div>
    </div>
  );
}
