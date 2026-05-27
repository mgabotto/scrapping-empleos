import {
  ArrowUpDownIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  DownloadIcon,
  ExternalLinkIcon,
  SearchIcon,
  Trash2Icon,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Job, JobStats } from "../types";

const SOURCE_COLORS: Record<string, string> = {
  linkedin: "bg-blue-100 text-blue-700",
  indeed: "bg-purple-100 text-purple-700",
  bumeran: "bg-orange-100 text-orange-700",
  zonajobs: "bg-teal-100 text-teal-700",
};

type SortKey = "titulo" | "empresa" | "ubicacion" | "fuente" | "fecha";

function SortIcon({ col, current, dir }: { col: SortKey; current: SortKey; dir: "asc" | "desc" }) {
  if (col !== current) return <ArrowUpDownIcon size={13} className="text-gray-300 ml-1 inline" />;
  return dir === "asc"
    ? <ChevronUpIcon size={13} className="text-rose-500 ml-1 inline" />
    : <ChevronDownIcon size={13} className="text-rose-500 ml-1 inline" />;
}

function exportCSV(jobs: Job[]) {
  const headers = ["Fuente", "Título", "Empresa", "Ubicación", "Modalidad", "Salario", "Fecha", "URL"];
  const rows = jobs.map((j) => [
    j.fuente ?? "",
    j.titulo ?? "",
    j.empresa ?? "",
    j.ubicacion ?? "",
    j.modalidad ?? (j.es_remoto ? "Remoto" : ""),
    j.salario ?? "",
    j.fecha ?? "",
    j.url ?? "",
  ]);
  const csv = [headers, ...rows]
    .map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `empleos_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<JobStats | null>(null);
  const [search, setSearch] = useState("");
  const [fuente, setFuente] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("fecha");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await api.getJobs({
        fuente: fuente || undefined,
        search: search || undefined,
      });
      setJobs(data);
    } catch {}
  }, [fuente, search]);

  const fetchStats = useCallback(async () => {
    try {
      setStats(await api.getStats());
    } catch {}
  }, []);

  useEffect(() => {
    fetchJobs();
    fetchStats();
  }, [fetchJobs, fetchStats]);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(fetchJobs, 300);
    return () => clearTimeout(t);
  }, [search, fetchJobs]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  const sorted = [...jobs].sort((a, b) => {
    const va = String(a[sortKey] ?? "").toLowerCase();
    const vb = String(b[sortKey] ?? "").toLowerCase();
    return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
  });

  async function handleClear() {
    if (!confirm("¿Eliminar todos los empleos?")) return;
    await api.clearJobs();
    setJobs([]);
    await fetchStats();
  }

  const sources = stats ? Object.keys(stats.by_source) : [];

  return (
    <div className="px-6 py-8 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">💼 Empleos</h2>
          <p className="text-gray-500 mt-1 text-sm">
            {stats
              ? `${stats.total} ofertas encontradas` +
                (Object.keys(stats.by_source).length
                  ? " — " + Object.entries(stats.by_source).map(([s, c]) => `${s}: ${c}`).join(" · ")
                  : "")
              : "Cargando..."}
          </p>
        </div>
        <div className="flex gap-2">
          {jobs.length > 0 && (
            <button
              onClick={() => exportCSV(sorted)}
              className="flex items-center gap-2 border border-gray-300 text-gray-700 hover:bg-gray-50 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <DownloadIcon size={15} /> Exportar CSV
            </button>
          )}
          {jobs.length > 0 && (
            <button
              onClick={handleClear}
              className="flex items-center gap-2 border border-red-200 text-red-600 hover:bg-red-50 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <Trash2Icon size={15} /> Limpiar
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <div className="relative flex-1 max-w-xs">
          <SearchIcon size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar por título o empresa..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full border border-gray-300 rounded-lg pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-400"
          />
        </div>
        <select
          value={fuente}
          onChange={(e) => setFuente(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-rose-400"
        >
          <option value="">Todas las fuentes</option>
          {sources.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        {(search || fuente) && (
          <button
            onClick={() => { setSearch(""); setFuente(""); }}
            className="text-sm text-gray-500 hover:text-gray-700 px-2"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Table */}
      {sorted.length === 0 && jobs.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-400 py-20">
          <p className="text-5xl mb-4">🔍</p>
          <p className="font-medium text-gray-600">No hay ofertas todavía</p>
          <p className="text-sm mt-1">Andá a <strong>Buscadores</strong> y ejecutá una búsqueda</p>
        </div>
      ) : (
        <div className="flex-1 overflow-auto rounded-xl border border-gray-200 shadow-sm">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-28">
                  <button onClick={() => handleSort("fuente")} className="flex items-center hover:text-gray-900">
                    Fuente <SortIcon col="fuente" current={sortKey} dir={sortDir} />
                  </button>
                </th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">
                  <button onClick={() => handleSort("titulo")} className="flex items-center hover:text-gray-900">
                    Título <SortIcon col="titulo" current={sortKey} dir={sortDir} />
                  </button>
                </th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-40">
                  <button onClick={() => handleSort("empresa")} className="flex items-center hover:text-gray-900">
                    Empresa <SortIcon col="empresa" current={sortKey} dir={sortDir} />
                  </button>
                </th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-36">
                  <button onClick={() => handleSort("ubicacion")} className="flex items-center hover:text-gray-900">
                    Ubicación <SortIcon col="ubicacion" current={sortKey} dir={sortDir} />
                  </button>
                </th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-28">
                  <button onClick={() => handleSort("fecha")} className="flex items-center hover:text-gray-900">
                    Fecha <SortIcon col="fecha" current={sortKey} dir={sortDir} />
                  </button>
                </th>
                <th className="px-4 py-3 w-14" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((job, idx) => {
                const isExpanded = expandedId === job.id;
                const sourceKey = (job.fuente ?? "").toLowerCase();
                return (
                  <>
                    <tr
                      key={job.id}
                      className={`border-b border-gray-100 cursor-pointer transition-colors ${
                        idx % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                      } hover:bg-rose-50/40`}
                      onClick={() => setExpandedId(isExpanded ? null : job.id)}
                    >
                      <td className="px-4 py-3">
                        <span
                          className={`text-xs font-semibold px-2 py-0.5 rounded-full whitespace-nowrap ${
                            SOURCE_COLORS[sourceKey] ?? "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {job.fuente}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-medium text-gray-900 line-clamp-2 leading-snug">
                          {job.titulo ?? "—"}
                        </span>
                        {job.salario && (
                          <span className="text-xs text-green-700 font-medium mt-0.5 block">{job.salario}</span>
                        )}
                        {job.es_remoto && (
                          <span className="text-xs bg-rose-100 text-rose-600 px-1.5 py-0.5 rounded mt-0.5 inline-block">
                            Remoto
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600 max-w-[160px] truncate">{job.empresa ?? "—"}</td>
                      <td className="px-4 py-3 text-gray-600 max-w-[144px] truncate">{job.ubicacion ?? "—"}</td>
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{job.fecha ? String(job.fecha) : "—"}</td>
                      <td className="px-4 py-3 text-center">
                        {job.url && (
                          <a
                            href={job.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-rose-500 hover:text-rose-600 inline-flex items-center justify-center"
                            title="Ver oferta"
                          >
                            <ExternalLinkIcon size={16} />
                          </a>
                        )}
                      </td>
                    </tr>
                    {isExpanded && job.descripcion && (
                      <tr key={`${job.id}-desc`} className="bg-rose-50/30 border-b border-gray-100">
                        <td colSpan={6} className="px-6 py-3">
                          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Descripción</p>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                            {job.descripcion}
                          </p>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-gray-400 mt-2 text-right">{sorted.length} resultado{sorted.length !== 1 ? "s" : ""}</p>
    </div>
  );
}
