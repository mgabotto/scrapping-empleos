import { AlertCircleIcon, CheckCircleIcon, ChevronDownIcon, ChevronUpIcon, ClockIcon, PlayIcon, RefreshCwIcon } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Run, ScraperInfo } from "../types";

type RunState = { runId: string; run: Run } | null;

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className="bg-rose-500 h-2 rounded-full transition-all duration-500"
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

function LinkedInConfig({
  config,
  onChange,
}: {
  config: Record<string, unknown>;
  onChange: (c: Record<string, unknown>) => void;
}) {
  const terminos = (config.terminos as string[]) ?? [];

  return (
    <div className="space-y-3 text-sm">
      <div>
        <label className="block font-medium text-gray-700 mb-1">Términos de búsqueda (uno por línea)</label>
        <textarea
          rows={4}
          value={terminos.join("\n")}
          onChange={(e) =>
            onChange({ ...config, terminos: e.target.value.split("\n").map((s) => s.trim()).filter(Boolean) })
          }
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-rose-400 resize-none"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block font-medium text-gray-700 mb-1">Ubicación</label>
          <input
            type="text"
            value={(config.ubicacion as string) ?? ""}
            onChange={(e) => onChange({ ...config, ubicacion: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-rose-400"
          />
        </div>
        <div>
          <label className="block font-medium text-gray-700 mb-1">Horas atrás</label>
          <input
            type="number"
            min={1}
            value={(config.horas_atras as number) ?? 96}
            onChange={(e) => onChange({ ...config, horas_atras: Number(e.target.value) })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-rose-400"
          />
        </div>
        <div>
          <label className="block font-medium text-gray-700 mb-1">Resultados por búsqueda</label>
          <input
            type="number"
            min={5}
            max={100}
            value={(config.resultados_por_busqueda as number) ?? 30}
            onChange={(e) => onChange({ ...config, resultados_por_busqueda: Number(e.target.value) })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-rose-400"
          />
        </div>
        <div className="flex items-end pb-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={(config.is_remote as boolean) ?? false}
              onChange={(e) => onChange({ ...config, is_remote: e.target.checked })}
              className="rounded"
            />
            <span className="font-medium text-gray-700">Solo remotos</span>
          </label>
        </div>
      </div>
      <div>
        <label className="block font-medium text-gray-700 mb-1">Sitios</label>
        <div className="flex gap-4">
          {["linkedin", "indeed"].map((site) => (
            <label key={site} className="flex items-center gap-2 cursor-pointer capitalize">
              <input
                type="checkbox"
                checked={((config.sitios as string[]) ?? []).includes(site)}
                onChange={(e) => {
                  const current = (config.sitios as string[]) ?? [];
                  onChange({
                    ...config,
                    sitios: e.target.checked ? [...current, site] : current.filter((s) => s !== site),
                  });
                }}
                className="rounded"
              />
              {site}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}

function ArgentinaConfig({
  config,
  onChange,
}: {
  config: Record<string, unknown>;
  onChange: (c: Record<string, unknown>) => void;
}) {
  const terminos = (config.terminos as string[]) ?? [];
  const tiempoEstimado = terminos.length * 15;
  return (
    <div className="space-y-3 text-sm">
      {/* Advertencia de tiempo */}
      <div className="flex gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5 text-amber-800">
        <ClockIcon size={15} className="flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-medium">Scraper lento — usá pocos términos</p>
          <p className="text-xs mt-0.5">
            Cada término tarda ~15 min con descripciones.{" "}
            {terminos.length > 0 && (
              <span className="font-semibold">
                Con {terminos.length} término{terminos.length !== 1 ? "s" : ""}: ~{tiempoEstimado} min estimados.
              </span>
            )}
          </p>
        </div>
      </div>

      <div>
        <label className="block font-medium text-gray-700 mb-1">
          Términos de búsqueda{" "}
          <span className="text-amber-600 font-normal">(recomendado: 1-2 máximo)</span>
        </label>
        <textarea
          rows={4}
          value={terminos.join("\n")}
          onChange={(e) =>
            onChange({ ...config, terminos: e.target.value.split("\n").map((s) => s.trim()).filter(Boolean) })
          }
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-rose-400 resize-none"
          placeholder="Un término por línea&#10;Ej: Marketing"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block font-medium text-gray-700 mb-1">Páginas por búsqueda</label>
          <input
            type="number"
            min={1}
            max={10}
            value={(config.paginas_por_busqueda as number) ?? 3}
            onChange={(e) => onChange({ ...config, paginas_por_busqueda: Number(e.target.value) })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-rose-400"
          />
        </div>
        <div className="flex items-end pb-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={(config.obtener_descripcion as boolean) ?? true}
              onChange={(e) => onChange({ ...config, obtener_descripcion: e.target.checked })}
              className="rounded"
            />
            <span className="font-medium text-gray-700">Descargar descripciones</span>
          </label>
        </div>
      </div>
      <p className="text-xs text-gray-400">
        Con descripciones: ~15 min/término · Sin descripciones: ~2-3 min en total
      </p>
    </div>
  );
}

function ScraperCard({ info, onJobsUpdated }: { info: ScraperInfo; onJobsUpdated: () => void }) {
  const [config, setConfig] = useState<Record<string, unknown>>(info.default_config);
  const [showConfig, setShowConfig] = useState(false);
  const [runState, setRunState] = useState<RunState>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const isRunning = runState?.run.status === "running";

  const stopPolling = useCallback(() => {
    if (pollRef.current != null) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPolling = useCallback(
    (runId: string) => {
      stopPolling();
      pollRef.current = window.setInterval(async () => {
        try {
          const run = await api.getRun(runId);
          setRunState({ runId, run });
          if (run.status !== "running") {
            stopPolling();
            if (run.status === "completed") onJobsUpdated();
          }
        } catch {
          stopPolling();
        }
      }, 2000);
    },
    [stopPolling, onJobsUpdated]
  );

  useEffect(() => () => stopPolling(), [stopPolling]);

  // Resume polling if there was a running scraper on mount
  useEffect(() => {
    const lr = info.last_run;
    if (lr?.status === "running" && lr.id) {
      setRunState({ runId: lr.id, run: lr });
      startPolling(lr.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleRun() {
    setError(null);
    try {
      const { run_id } = await api.runScraper(info.id, config);
      const run = await api.getRun(run_id);
      setRunState({ runId: run_id, run });
      startPolling(run_id);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const currentRun = runState?.run ?? info.last_run;
  const progress = runState?.run.progress ?? (currentRun?.status !== "running" ? 100 : 0);
  const message = runState?.run.message ?? "";

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{info.nombre}</h3>
          <p className="text-sm text-gray-500 mt-0.5">{info.descripcion}</p>
          {info.id === "argentina" && (
            <p className="text-xs text-amber-600 mt-1.5 flex items-center gap-1">
              <ClockIcon size={12} />
              ~15 min por término de búsqueda — usá pocos términos
            </p>
          )}
        </div>
        <button
          onClick={handleRun}
          disabled={isRunning}
          className="flex items-center gap-2 bg-rose-500 hover:bg-rose-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors flex-shrink-0"
        >
          {isRunning ? (
            <><RefreshCwIcon size={15} className="animate-spin" /> Ejecutando...</>
          ) : (
            <><PlayIcon size={15} /> Ejecutar</>
          )}
        </button>
      </div>

      {/* Progress */}
      {isRunning && (
        <div className="mt-4 space-y-2">
          <ProgressBar value={progress} />
          <p className="text-xs text-gray-500">{message}</p>
        </div>
      )}

      {/* Last run result */}
      {currentRun && !isRunning && (
        <div className={`mt-4 flex items-center gap-2 text-sm rounded-lg px-3 py-2 ${
          currentRun.status === "completed"
            ? "bg-green-50 text-green-700"
            : currentRun.status === "failed"
            ? "bg-red-50 text-red-700"
            : "bg-gray-50 text-gray-600"
        }`}>
          {currentRun.status === "completed" ? (
            <CheckCircleIcon size={15} />
          ) : (
            <AlertCircleIcon size={15} />
          )}
          {currentRun.status === "completed" ? (
            <>Último scrape: <strong>{currentRun.total_jobs}</strong> empleos ({currentRun.new_jobs} nuevos)</>
          ) : currentRun.status === "failed" ? (
            <>Error: {currentRun.error ?? "desconocido"}</>
          ) : null}
        </div>
      )}

      {error && (
        <div className="mt-3 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 flex items-center gap-2">
          <AlertCircleIcon size={15} /> {error}
        </div>
      )}

      {/* Config toggle */}
      <button
        onClick={() => setShowConfig(!showConfig)}
        className="mt-4 flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
      >
        {showConfig ? <ChevronUpIcon size={13} /> : <ChevronDownIcon size={13} />}
        {showConfig ? "Ocultar configuración" : "Configurar búsqueda"}
      </button>

      {showConfig && (
        <div className="mt-3 border-t border-gray-100 pt-4">
          {info.id === "linkedin" ? (
            <LinkedInConfig config={config} onChange={setConfig} />
          ) : (
            <ArgentinaConfig config={config} onChange={setConfig} />
          )}
        </div>
      )}
    </div>
  );
}

const DEFAULT_SCRAPERS: ScraperInfo[] = [
  {
    id: "linkedin",
    nombre: "LinkedIn & Indeed",
    descripcion: "Scraper vía jobspy para LinkedIn e Indeed",
    default_config: {
      terminos: ["PR", "Marketing", "Comunicación Institucional", "Comunicación Externa"],
      sitios: ["linkedin", "indeed"],
      ubicacion: "Argentina",
      resultados_por_busqueda: 30,
      horas_atras: 96,
      is_remote: false,
    },
  },
  {
    id: "argentina",
    nombre: "ZonaJobs & Bumeran",
    descripcion: "Scraper Selenium para ZonaJobs y Bumeran (Argentina)",
    default_config: {
      terminos: ["PR", "Marketing", "Comunicación Institucional", "Comunicación Externa"],
      paginas_por_busqueda: 3,
      obtener_descripcion: true,
    },
  },
];

export default function ScrapersPage() {
  const [scrapers, setScrapers] = useState<ScraperInfo[]>(DEFAULT_SCRAPERS);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    api.getScrapers().then(setScrapers).catch(() => {});
  }, [refresh]);

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">🔍 Buscadores</h2>
        <p className="text-gray-500 mt-1">Buscá ofertas de empleo en múltiples plataformas.</p>
      </div>

      <div className="space-y-4">
        {scrapers.map((s) => (
          <ScraperCard key={s.id} info={s} onJobsUpdated={() => setRefresh((r) => r + 1)} />
        ))}
      </div>
    </div>
  );
}
