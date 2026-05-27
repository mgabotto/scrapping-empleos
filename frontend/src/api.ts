import type { Job, JobStats, Profile, Run, ScraperInfo } from "./types";

// En producción (Vercel) usar la URL del backend en Render; en dev usar el proxy de Vite
const BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Profile
  getProfile: () => req<Profile>("/profile"),
  updateProfile: (data: Profile) =>
    req<Profile>("/profile", { method: "PUT", body: JSON.stringify(data) }),

  // Scrapers
  getScrapers: () => req<ScraperInfo[]>("/scrapers"),
  runScraper: (id: string, config?: Record<string, unknown>) =>
    req<{ run_id: string }>(`/scrapers/${id}/run`, {
      method: "POST",
      body: JSON.stringify(config ?? null),
    }),
  getRun: (id: string) => req<Run>(`/runs/${id}`),

  // Jobs
  getJobs: (params?: { fuente?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.fuente) q.set("fuente", params.fuente);
    if (params?.search) q.set("search", params.search);
    const qs = q.toString();
    return req<Job[]>(`/jobs${qs ? "?" + qs : ""}`);
  },
  getStats: () => req<JobStats>("/jobs/stats"),
  clearJobs: () => req<{ deleted: number }>("/jobs", { method: "DELETE" }),
};
