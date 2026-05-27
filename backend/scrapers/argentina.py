"""Scraper ZonaJobs & Bumeran via Selenium — adaptado para devolver datos en vez de Excel."""
import sys
import time
import uuid
from typing import Callable, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

DEFAULT_CONFIG = {
    "terminos": ["PR", "Marketing", "Comunicación Institucional", "Comunicación Externa"],
    "paginas_por_busqueda": 3,
    "obtener_descripcion": True,
    "demora_entre_requests": 3,
}


def run(config: Optional[Dict] = None, progress_callback: Optional[Callable] = None) -> List[Dict]:
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    terminos = cfg["terminos"]
    paginas = cfg["paginas_por_busqueda"]
    obtener_desc = cfg["obtener_descripcion"]

    driver = _iniciar_driver()
    todos: List[Dict] = []
    total_terminos = len(terminos)

    try:
        for i, termino in enumerate(terminos):
            pct_base = int(i / total_terminos * (65 if obtener_desc else 90))
            if progress_callback:
                progress_callback(pct_base, f"Buscando '{termino}' en Bumeran...")

            todos.extend(_scrapear_bumeran(driver, termino, paginas, cfg.get("demora_entre_requests", 3)))
            time.sleep(2)

            if progress_callback:
                progress_callback(pct_base + 5, f"Buscando '{termino}' en ZonaJobs...")
            todos.extend(_scrapear_zonajobs(driver, termino, paginas, cfg.get("demora_entre_requests", 3)))
            time.sleep(2)

        # Deduplicar
        seen: set = set()
        unique = []
        for emp in todos:
            if emp["url"] and emp["url"] not in seen:
                seen.add(emp["url"])
                unique.append(emp)

        if obtener_desc and unique:
            if progress_callback:
                progress_callback(68, f"Descargando descripciones de {len(unique)} avisos...")
            for j, empleo in enumerate(unique):
                if empleo.get("url"):
                    empleo["descripcion"] = _obtener_descripcion(driver, empleo["url"])
                if progress_callback:
                    pct = 68 + int((j + 1) / len(unique) * 30)
                    progress_callback(pct, f"Descripción {j + 1}/{len(unique)}: {(empleo.get('titulo') or '')[:45]}...")

        if progress_callback:
            progress_callback(100, f"Completado: {len(unique)} empleos únicos")

        return unique

    finally:
        driver.quit()


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _iniciar_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    # En Linux (Docker/Render) apuntar al Chrome del sistema
    if sys.platform != "win32":
        opts.binary_location = "/usr/bin/google-chrome"
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def _scrapear_bumeran(driver, termino: str, max_paginas: int, demora: int) -> List[Dict]:
    return _scrapear_navent(driver, termino, max_paginas, demora, "Bumeran", "bumeran.com.ar")


def _scrapear_zonajobs(driver, termino: str, max_paginas: int, demora: int) -> List[Dict]:
    return _scrapear_navent(driver, termino, max_paginas, demora, "ZonaJobs", "zonajobs.com.ar")


def _scrapear_navent(driver, termino: str, max_paginas: int, demora: int, fuente: str, dominio: str) -> List[Dict]:
    empleos: List[Dict] = []
    termino_url = termino.lower().replace(" ", "-")

    for pagina in range(1, max_paginas + 1):
        url = f"https://www.{dominio}/empleos-busqueda-{termino_url}.html?page={pagina}"
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "main#listado-avisos, main[aria-label*='avisos']")
                )
            )
            time.sleep(demora)

            tarjetas = driver.find_elements(
                By.CSS_SELECTOR,
                "a[aria-labelledby*='job-posting'], a[href*='/empleos/']",
            )
            if not tarjetas:
                tarjetas_raw = driver.find_elements(
                    By.CSS_SELECTOR, "[data-col-job-posting], [id*='header-col-job-posting']"
                )
                tarjetas = [t.find_element(By.XPATH, "ancestor::a[1]") for t in tarjetas_raw if t]

            if not tarjetas:
                break

            vistos: set = set()
            for tarjeta in tarjetas:
                try:
                    url_aviso = tarjeta.get_attribute("href") or ""
                    if url_aviso in vistos:
                        continue
                    vistos.add(url_aviso)

                    titulo = _texto_seguro(tarjeta, ["h2", "h3", "[class*='dPSvQ']", "[class*='gIOnpy']"])
                    empresa = _texto_seguro(tarjeta, [
                        "[class*='buGlAa']:nth-child(2)", "[class*='company']",
                        "[class*='empresa']", "div[class*='sc-'] span",
                    ])
                    ubicacion = _texto_seguro(tarjeta, [
                        "[id*='footer-col-job-posting'] span", "[class*='dzQEYZ'] span",
                        "[class*='location']", "[class*='ubicacion']",
                    ])
                    fecha = _texto_seguro(tarjeta, [
                        "[class*='bpubUI']", "[class*='date']", "[class*='fecha']", "time",
                    ])

                    if titulo:
                        empleos.append({
                            "id": str(uuid.uuid4()),
                            "fuente": fuente,
                            "termino_busqueda": termino,
                            "titulo": titulo,
                            "empresa": empresa or None,
                            "ubicacion": ubicacion or None,
                            "fecha": fecha or None,
                            "url": url_aviso,
                            "descripcion": None,
                            "salario": None,
                            "modalidad": None,
                            "es_remoto": False,
                        })
                except Exception:
                    continue
        except Exception:
            break

    return empleos


def _obtener_descripcion(driver, url_aviso: str) -> Optional[str]:
    es_selecta = "selecta" in url_aviso.lower()
    sleep_inicial = 4.0 if es_selecta else 1.5
    timeout = 20 if es_selecta else 15

    try:
        driver.get(url_aviso)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div#ficha-detalle, div#section-detalle")
            )
        )
        time.sleep(sleep_inicial)

        # Caso iframe (Selecta)
        try:
            iframe = driver.find_element(
                By.CSS_SELECTOR, "div#ficha-detalle iframe, div#section-detalle iframe"
            )
            driver.switch_to.frame(iframe)
            texto = driver.find_element(By.CSS_SELECTOR, "body").text.strip()
            driver.switch_to.default_content()
            if len(texto) > 100:
                return texto[:3000]
        except Exception:
            driver.switch_to.default_content()

        # Esperar contenido lazy
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: len(
                    d.find_element(By.CSS_SELECTOR, "div#ficha-detalle, div#section-detalle").text.strip()
                ) > 50
            )
        except Exception:
            pass

        for selector in [
            "div#ficha-detalle", "div#section-detalle",
            "div[data-testid='job-description']", "div[class*='JobDescription']",
            "div[class*='bGXeph']", "div[class*='duqfIc']",
            "div[class*='description']", "div[class*='descripcion']",
            "article[class*='job']", "main section",
        ]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                texto = elem.text.strip()
                if len(texto) > 100:
                    return texto[:3000]
            except Exception:
                continue
    except Exception:
        pass

    return None


def _texto_seguro(elemento, selectores: List[str]) -> str:
    for selector in selectores:
        try:
            elem = elemento.find_element(By.CSS_SELECTOR, selector)
            texto = elem.text.strip()
            if texto:
                return texto
        except Exception:
            continue
    return ""
