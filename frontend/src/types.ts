export interface Job {
  id: string;
  fuente?: string;
  termino_busqueda?: string;
  titulo?: string;
  empresa?: string;
  ubicacion?: string;
  fecha?: string;
  url?: string;
  descripcion?: string;
  salario?: string;
  modalidad?: string;
  es_remoto?: boolean;
  run_id?: string;
  created_at?: string;
  ai_score?: number;
  ai_justificacion?: string;
  ai_tags?: string;
  ai_analyzed_at?: string;
}

export interface Profile {
  id?: number;
  nombre: string;
  skills: string;
  experiencia_anos: number;
  nivel: string;
  modalidad_preferida: string;
  otras_preferencias: string;
}

export interface Run {
  id: string;
  scraper_id: string;
  status: string;
  started_at?: string;
  finished_at?: string;
  total_jobs: number;
  new_jobs: number;
  error?: string;
  progress?: number;
  message?: string;
}

export interface ScraperInfo {
  id: string;
  nombre: string;
  descripcion: string;
  default_config: Record<string, unknown>;
  last_run?: Run;
}

export interface JobStats {
  total: number;
  by_source: Record<string, number>;
}
