"""Scraper Computrabajo Argentina — requests + BeautifulSoup (sin Selenium, sin Chrome)."""
import time
import uuid
from typing import Callable, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

DEFAULT_CONFIG = {
    "terminos": ["PR", "Marketing", "Comunicación Institucional", "Comunicación Externa"],
    "paginas_por_busqueda": 3,
    "obtener_descripcion": False,
}

BASE_URL = "https://ar.computrabajo.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}


def _slugify(texto: str) -> str:
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u",
        "ñ": "n", "Ñ": "n", "ü": "u", "Ü": "u",
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto.lower().replace(" ", "-")


def run(config: Optional[Dict] = None, progress_callback: Optional[Callable] = None) -> List[Dict]:
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    terminos = cfg["terminos"]
    paginas = cfg["paginas_por_busqueda"]
    obtener_desc = cfg["obtener_descripcion"]

    session = requests.Session()
    session.headers.update(HEADERS)

    todos: List[Dict] = []
    total = len(terminos)

    for i, termino in enumerate(terminos):
        pct_base = int(i / total * (80 if obtener_desc else 95))
        if progress_callback:
            progress_callback(pct_base, f"Buscando '{termino}' en Computrabajo...")

        empleos = _scrapear_termino(session, termino, paginas)
        todos.extend(empleos)

        if progress_callback:
            progress_callback(pct_base + 5, f"'{termino}': {len(empleos)} avisos encontrados")

        time.sleep(1)

    # Deduplicar por URL
    seen: set = set()
    unique = []
    for emp in todos:
        url = emp.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(emp)

    if obtener_desc and unique:
        if progress_callback:
            progress_callback(82, f"Descargando descripciones de {len(unique)} avisos...")
        for j, empleo in enumerate(unique):
            if empleo.get("url"):
                empleo["descripcion"] = _obtener_descripcion(session, empleo["url"])
                time.sleep(0.5)
            if progress_callback:
                pct = 82 + int((j + 1) / len(unique) * 16)
                progress_callback(pct, f"Desc {j + 1}/{len(unique)}: {empleo.get('titulo', '')[:40]}...")

    if progress_callback:
        progress_callback(100, f"Completado: {len(unique)} empleos únicos en Computrabajo")

    return unique


def _scrapear_termino(session: requests.Session, termino: str, max_paginas: int) -> List[Dict]:
    slug = _slugify(termino)
    empleos: List[Dict] = []

    for pagina in range(1, max_paginas + 1):
        url = f"{BASE_URL}/trabajo-de-{slug}?p={pagina}" if pagina > 1 else f"{BASE_URL}/trabajo-de-{slug}"
        try:
            resp = session.get(url, timeout=20)
            print(f"[Computrabajo] '{termino}' p{pagina} → HTTP {resp.status_code} ({len(resp.text)} bytes)", flush=True)

            if resp.status_code != 200:
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = _extraer_cards(soup, termino)

            print(f"[Computrabajo] '{termino}' p{pagina} → {len(cards)} avisos extraídos", flush=True)

            if not cards:
                break

            empleos.extend(cards)
            time.sleep(1)

        except Exception as exc:
            print(f"[Computrabajo] error '{termino}' p{pagina}: {exc}", flush=True)
            break

    return empleos


def _extraer_cards(soup: BeautifulSoup, termino: str) -> List[Dict]:
    """Extrae avisos de empleo del HTML de Computrabajo.

    Estructura del card:
      <div>
        <a href="/ofertas-de-trabajo/oferta-de-...#lc=...">
          <h2 o h3>Título</h2>
        </a>
        <p>Empresa</p>
        <p>Ubicación | Modalidad</p>
        <p>Hace X horas</p>
      </div>
    """
    empleos: List[Dict] = []
    seen_urls: set = set()

    job_links = soup.select("a[href*='/ofertas-de-trabajo/']")

    for link in job_links:
        raw_href = link.get("href", "")
        if not raw_href:
            continue

        # Quitar el fragment de tracking (#lc=...)
        href_clean = raw_href.split("#")[0].strip()
        if not href_clean or href_clean in seen_urls:
            continue
        seen_urls.add(href_clean)

        full_url = href_clean if href_clean.startswith("http") else f"{BASE_URL}{href_clean}"

        # Título dentro del <a>
        titulo_elem = link.find(["h2", "h3"])
        titulo = titulo_elem.get_text(strip=True) if titulo_elem else link.get_text(strip=True).split("\n")[0].strip()
        if not titulo or len(titulo) < 3:
            continue

        # Empresa, ubicación y fecha son los <p> hermanos del <a>
        p_tags = link.find_next_siblings("p")

        empresa = p_tags[0].get_text(strip=True) if len(p_tags) > 0 else None
        ubicacion_raw = p_tags[1].get_text(strip=True) if len(p_tags) > 1 else None
        fecha = p_tags[2].get_text(strip=True) if len(p_tags) > 2 else None

        # "Buenos Aires, GBA | Presencial y remoto"
        ubicacion = None
        modalidad = None
        es_remoto = False
        if ubicacion_raw:
            partes = [p.strip() for p in ubicacion_raw.split("|")]
            ubicacion = partes[0] if partes else ubicacion_raw
            if len(partes) > 1:
                modalidad = partes[1]
                es_remoto = "remoto" in modalidad.lower()

        empleos.append({
            "id": str(uuid.uuid4()),
            "fuente": "Computrabajo",
            "termino_busqueda": termino,
            "titulo": titulo,
            "empresa": empresa or None,
            "ubicacion": ubicacion or None,
            "fecha": fecha or None,
            "url": full_url,
            "descripcion": None,
            "salario": None,
            "modalidad": modalidad or None,
            "es_remoto": es_remoto,
        })

    return empleos


def _obtener_descripcion(session: requests.Session, url: str) -> Optional[str]:
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        for selector in [
            "div[class*='description']",
            "div[class*='descripcion']",
            "section[class*='description']",
            "div[id*='description']",
            "article",
            "div.job-description",
            "main",
        ]:
            elem = soup.select_one(selector)
            if elem:
                texto = elem.get_text(separator="\n", strip=True)
                if len(texto) > 100:
                    return texto[:3000]
    except Exception:
        pass
    return None
