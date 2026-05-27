import { BriefcaseIcon, SearchIcon, SparklesIcon } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const nav = [
  { to: "/scrapers", icon: SearchIcon, label: "Buscadores" },
  { to: "/jobs", icon: BriefcaseIcon, label: "Empleos" },
];

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className="w-60 text-white flex flex-col flex-shrink-0"
        style={{ background: "linear-gradient(160deg, #4c1d95 0%, #7c3aed 45%, #be185d 100%)" }}
      >
        {/* Logo */}
        <div className="px-5 py-7 border-b border-white/10">
          <div className="flex items-center gap-2 mb-1">
            <SparklesIcon size={20} className="text-pink-300 flex-shrink-0" />
            <h1 className="text-base font-bold leading-tight tracking-wide">
              Buscador de Empleos
            </h1>
          </div>
          <p className="text-xs text-purple-200 mt-1 pl-7">
            Encontrá tu próximo trabajo ✨
          </p>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-5 space-y-1">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? "bg-white/20 text-white shadow-sm backdrop-blur-sm"
                    : "text-purple-200 hover:bg-white/10 hover:text-white"
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-white/10">
          <p className="text-xs text-purple-300">💼 Argentina · LinkedIn · Indeed</p>
          <p className="text-xs text-purple-300">🌐 Bumeran · ZonaJobs</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto bg-rose-50/30">
        <Outlet />
      </main>
    </div>
  );
}
