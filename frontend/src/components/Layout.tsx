import { BriefcaseIcon, PlayCircleIcon } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const nav = [
  { to: "/scrapers", icon: PlayCircleIcon, label: "Scrapers" },
  { to: "/jobs", icon: BriefcaseIcon, label: "Empleos" },
];

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 text-white flex flex-col flex-shrink-0">
        <div className="px-5 py-6 border-b border-gray-700">
          <h1 className="text-lg font-bold leading-tight">Buscador de<br />Empleos IA</h1>
          <p className="text-xs text-gray-400 mt-1">Scraping de empleos</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-indigo-600 text-white"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
