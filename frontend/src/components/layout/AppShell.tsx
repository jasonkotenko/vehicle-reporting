import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useConfig } from "@/context/ConfigContext";

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded px-3 py-2 text-sm font-medium ${
    isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
  }`;

export function AppShell() {
  const { user, logout, isAdmin } = useAuth();
  const { displayTimezone } = useConfig();

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div>
            <Link to="/roster" className="text-lg font-semibold text-slate-900">
              Village Vehicle Tracking
            </Link>
            <p className="text-xs text-slate-500">Times shown in {displayTimezone}</p>
          </div>
          <nav className="flex flex-wrap items-center gap-1">
            <NavLink to="/roster" className={navClass}>
              Roster
            </NavLink>
            <NavLink to="/vehicles" className={navClass}>
              Vehicles
            </NavLink>
            {isAdmin && (
              <>
                <NavLink to="/reports" className={navClass}>
                  Reports
                </NavLink>
                <NavLink to="/admin/cameras" className={navClass}>
                  Cameras
                </NavLink>
                <NavLink to="/admin/authorized" className={navClass}>
                  Authorized
                </NavLink>
                <NavLink to="/admin/users" className={navClass}>
                  Users
                </NavLink>
                <NavLink to="/admin/audit" className={navClass}>
                  Audit
                </NavLink>
              </>
            )}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-600">{user?.display_name}</span>
            <button
              type="button"
              onClick={() => logout()}
              className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-50"
            >
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
