import { Building2Icon, CalendarIcon, ChevronDownIcon, ChevronUpIcon, ExternalLinkIcon, MapPinIcon } from "lucide-react";
import { useState } from "react";
import type { Job } from "../types";

const SOURCE_COLORS: Record<string, string> = {
  linkedin: "bg-blue-100 text-blue-700",
  indeed: "bg-purple-100 text-purple-700",
  bumeran: "bg-orange-100 text-orange-700",
  zonajobs: "bg-teal-100 text-teal-700",
};

function scoreColor(score?: number) {
  if (score == null) return "bg-gray-100 text-gray-500";
  if (score >= 80) return "bg-green-100 text-green-700";
  if (score >= 60) return "bg-yellow-100 text-yellow-700";
  if (score >= 40) return "bg-orange-100 text-orange-700";
  return "bg-red-100 text-red-600";
}

function scoreBorder(score?: number) {
  if (score == null) return "border-gray-200";
  if (score >= 80) return "border-l-green-400";
  if (score >= 60) return "border-l-yellow-400";
  if (score >= 40) return "border-l-orange-400";
  return "border-l-red-400";
}

export default function JobCard({ job }: { job: Job }) {
  const [expanded, setExpanded] = useState(false);

  const tags: string[] = (() => {
    try {
      return job.ai_tags ? JSON.parse(job.ai_tags) : [];
    } catch {
      return [];
    }
  })();

  const sourceKey = (job.fuente ?? "").toLowerCase();
  const sourceClass = SOURCE_COLORS[sourceKey] ?? "bg-gray-100 text-gray-600";

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-l-4 ${scoreBorder(job.ai_score)} p-5 hover:shadow-md transition-shadow`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${sourceClass}`}>
              {job.fuente}
            </span>
            {job.es_remoto && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                Remoto
              </span>
            )}
          </div>

          <h3 className="font-semibold text-gray-900 text-base leading-tight">
            {job.titulo ?? "Sin título"}
          </h3>

          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-sm text-gray-500">
            {job.empresa && (
              <span className="flex items-center gap-1">
                <Building2Icon size={13} /> {job.empresa}
              </span>
            )}
            {job.ubicacion && (
              <span className="flex items-center gap-1">
                <MapPinIcon size={13} /> {job.ubicacion}
              </span>
            )}
            {job.fecha && (
              <span className="flex items-center gap-1">
                <CalendarIcon size={13} /> {String(job.fecha)}
              </span>
            )}
            {job.salario && (
              <span className="text-green-700 font-medium">{job.salario}</span>
            )}
          </div>
        </div>

        {/* Score badge */}
        <div className={`flex-shrink-0 w-14 h-14 rounded-xl flex flex-col items-center justify-center ${scoreColor(job.ai_score)}`}>
          {job.ai_score != null ? (
            <>
              <span className="text-xl font-bold leading-none">{job.ai_score}</span>
              <span className="text-xs mt-0.5">score</span>
            </>
          ) : (
            <span className="text-xs text-center leading-tight">sin análisis</span>
          )}
        </div>
      </div>

      {/* AI justification */}
      {job.ai_justificacion && (
        <p className="mt-3 text-sm text-gray-600 italic border-l-2 border-indigo-200 pl-3">
          {job.ai_justificacion}
        </p>
      )}

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {tags.map((tag) => (
            <span key={tag} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Expandable description + link */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex gap-3">
          {job.url && (
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium"
            >
              <ExternalLinkIcon size={13} /> Ver oferta
            </a>
          )}
          {job.descripcion && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
            >
              {expanded ? <ChevronUpIcon size={13} /> : <ChevronDownIcon size={13} />}
              {expanded ? "Ocultar" : "Ver descripción"}
            </button>
          )}
        </div>
        {job.termino_busqueda && (
          <span className="text-xs text-gray-400">"{job.termino_busqueda}"</span>
        )}
      </div>

      {expanded && job.descripcion && (
        <div className="mt-3 text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 rounded-lg p-3 max-h-60 overflow-y-auto border border-gray-100">
          {job.descripcion}
        </div>
      )}
    </div>
  );
}
