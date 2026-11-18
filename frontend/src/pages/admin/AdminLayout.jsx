import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../auth.jsx";

const LINKS = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/upload", label: "Upload Students" },
  { to: "/admin/template", label: "ID Card Template" },
  { to: "/admin/generate", label: "Excel & ID Generation" },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const link = ({ isActive }) =>
    `block whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium ${isActive ? "bg-brand text-white" : "text-ink hover:bg-brand-tint"}`;
  return (
    <div className="min-h-screen md:flex">
      <aside className="border-b border-line bg-white md:min-h-screen md:w-60 md:shrink-0 md:border-b-0 md:border-r">
        <div className="flex items-center justify-between px-4 py-3 md:block">
          <div>
            <p className="font-bold text-brand">Hostel ID Cards</p>
            <p className="text-xs text-muted">IGDTUW Hostel Department</p>
          </div>
          <button onClick={logout} className="btn-ghost !py-1 md:mt-4 md:w-full">Sign out</button>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 pb-3 md:block md:space-y-1" aria-label="Admin sections">
          {LINKS.map((l) => <NavLink key={l.to} to={l.to} end={l.end} className={link}>{l.label}</NavLink>)}
        </nav>
      </aside>
      <main className="min-w-0 flex-1 p-4 md:p-8"><Outlet context={{ user }} /></main>
    </div>
  );
}
