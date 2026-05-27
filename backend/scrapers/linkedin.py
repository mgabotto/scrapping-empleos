"""Scraper LinkedIn & Indeed via jobspy — adaptado para devolver datos en vez de Excel."""
import uuid
from typing import Callable, Dict, List, Optional

import pandas as pd
from jobspy import scrape_jobs

DEFAULT_CONFIG = {
    "terminos": ["PR", "Marketing", "Comunicación Institucional", "Comunicación Externa"],
    "sitios": ["linkedin", "indeed"],
    "ubicacion": "Argentina",
    "resultados_por_busqueda": 30,
    "horas_atras": 96,
    "is_remote": False,
    "country_indeed": "Argentina",
}


def run(config: Optional[Dict] = None, progress_callback: Optional[Callable] = None) -> List[Dict]:
    cfg = {**DEFAULT_CONFIG, **(config or {})}

    terminos = cfg["terminos"]
    total = len(terminos)
    todos: List[Dict] = []

    for i, termino in enumerate(terminos):
        if progress_callback:
            progress_callback(int(i / total * 90), f"Buscando: {termino}...")
        try:
            df = scrape_jobs(
                site_name=cfg["sitios"],
                search_term=termino,
                location=cfg["ubicacion"],
                results_wanted=cfg["resultados_por_busqueda"],
                hours_old=cfg["horas_atras"],
                country_indeed=cfg.get("country_indeed", "Argentina"),
                is_remote=cfg.get("is_remote", False),
            )
            for _, row in df.iterrows():
                todos.append(_normalizar(row, termino))
        except Exception as e:
            if progress_callback:
                progress_callback(None, f"Error en '{termino}': {e}")

    # Deduplicar por URL
    seen: set = set()
    unique = []
    for job in todos:
        if job["url"] and job["url"] not in seen:
            seen.add(job["url"])
            unique.append(job)

    if progress_callback:
        progress_callback(100, f"Completado: {len(unique)} empleos únicos encontrados")

    return unique


def _normalizar(row: pd.Series, termino: str) -> Dict:
    def safe(val):
        return str(val) if pd.notna(val) and val != "" else None

    salario = None
    if pd.notna(row.get("min_amount")) and pd.notna(row.get("max_amount")):
        cur = row.get("currency", "")
        salario = f"{row['min_amount']:.0f}–{row['max_amount']:.0f} {cur}".strip()

    return {
        "id": str(uuid.uuid4()),
        "fuente": (safe(row.get("site")) or "").capitalize(),
        "termino_busqueda": termino,
        "titulo": safe(row.get("title")),
        "empresa": safe(row.get("company")),
        "ubicacion": safe(row.get("location")),
        "fecha": safe(row.get("date_posted")),
        "url": safe(row.get("job_url")),
        "descripcion": safe(row.get("description")),
        "salario": salario,
        "modalidad": safe(row.get("job_type")),
        "es_remoto": bool(row.get("is_remote")) if pd.notna(row.get("is_remote")) else False,
    }
