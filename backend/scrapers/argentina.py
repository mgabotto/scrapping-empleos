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

DEFAULT_CONFIG = {
    "terminos": ["PR", "Marketing", "Comunicación Institucional", "Comunicación Externa"],
    "paginas_por_busqueda": 3,
    "obtener_descripcion": True,
    "demora_entre_requests": 3,
}

# Normaliza texto para URL (quita tildes, espacios→guiones)
def _slugify(texto: str) -> str:
    reemplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
                  "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u",
                  "ñ": "n", "Ñ": "n", "ü": "u", "Ü": "u"}
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto.lower().replace(" ", "-")


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

            todos.extend(_scrapear_navent(driver, termino, paginas, cfg.get("demora_entre_requests", 3), "Bumeran", "bumeran.com.ar", progress_callback))
            time.sleep(2)

            if progress_callback:
                progress_callback(pct_base + 5, f"Buscando '{termino}' en ZonaJobs...")
            todos.extend(_scrapear_navent(driver, termino, paginas, cfg.get("demora_entre_requests", 3), "ZonaJobs", "zonajobs.com.ar", progress_callback))
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
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    if sys.platform != "win32":
        # Linux/Docker: usar Chromium del sistema (siempre version-matched con chromium-driver)
        opts.binary_location = "/usr/bin/chromium"
        service = Service("/usr/bin/chromedriver")
    else:
        # Windows local: descargar ChromeDriver automáticamente
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def _esperar_pagina(driver, timeout: int = 30) -> None:
    """Espera a que el DOM esté listo y el contenido dinámico renderizado."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception:
        pass


def _scrapear_navent(
    driver,
    termino: str,
    max_paginas: int,
    demora: int,
    fuente: str,
    dominio: str,
    progress_callback: Optional[Callable] = None,
) -> List[Dict]:
    empleos: List[Dict] = []
    termino_slug = _slugify(termino)

    for pagina in range(1, max_paginas + 1):
        url = f"https://www.{dominio}/empleos-busqueda-{termino_slug}.html?page={pagina}"
        try:
            driver.get(url)
            _esperar_pagina(driver, timeout=30)
            # Dar tiempo extra al framework JS para renderizar los cards
            time.sleep(max(demora, 5))

            titulo_pagina = driver.title or ""
            url_actual = driver.current_url or url

            # Log diagnóstico visible en Render logs y en el UI
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                body_preview = body_text[:300].replace("\n", " ")
                total_links = len(driver.find_elements(By.TAG_NAME, "a"))
            except Exception:
                body_preview = "(no body)"
                total_links = 0

            print(f"[SCRAPER {fuente} p{pagina}] título='{titulo_pagina}' url={url_actual}", flush=True)
            print(f"[SCRAPER {fuente} p{pagina}] links_total={total_links} body={body_preview[:150]}", flush=True)
            if progress_callback:
                progress_callback(None, f"[{fuente} p{pagina}] '{titulo_pagina}' — {total_links} links — {body_preview[:80]}")

            # Detectar si hay bloqueo o CAPTCHA
            if any(w in titulo_pagina.lower() for w in ["captcha", "blocked", "403", "access denied"]):
                if progress_callback:
                    progress_callback(None, f"[{fuente}] Página bloqueada: {titulo_pagina}")
                break

            # Obtener links a avisos (selector más confiable: el patrón de URL nunca cambia)
            links_avisos = driver.find_elements(By.CSS_SELECTOR, "a[href*='/empleos/ver/']")
            print(f"[SCRAPER {fuente} p{pagina}] selector /empleos/ver/ → {len(links_avisos)}", flush=True)

            # Fallbacks progresivos si el selector principal no encuentra nada
            if not links_avisos:
                for fallback in [
                    "a[href*='/empleo/']",
                    "[data-testid*='job'] a",
                    "[data-testid*='aviso'] a",
                    "article a[href]",
                    "li a[href*='empleo']",
                ]:
                    links_avisos = driver.find_elements(By.CSS_SELECTOR, fallback)
                    if links_avisos:
                        print(f"[SCRAPER {fuente} p{pagina}] fallback '{fallback}' → {len(links_avisos)}", flush=True)
                        break

            # Último recurso: cualquier <a> cuya URL contenga el patrón de aviso
            if not links_avisos:
                todos_links = driver.find_elements(By.TAG_NAME, "a")
                links_avisos = [
                    l for l in todos_links
                    if "/empleos/ver/" in (l.get_attribute("href") or "")
                    or "/empleo/" in (l.get_attribute("href") or "")
                ]
                # Log todos los hrefs para diagnóstico
                hrefs = [l.get_attribute("href") for l in todos_links[:20]]
                print(f"[SCRAPER {fuente} p{pagina}] primeros hrefs: {hrefs}", flush=True)

            if not links_avisos:
                if progress_callback:
                    progress_callback(None, f"[{fuente} p{pagina}] Sin avisos. Ver logs de Render para diagnóstico.")
                break  # Sin más páginas

            vistos: set = set()
            for link in links_avisos:
                try:
                    url_aviso = link.get_attribute("href") or ""
                    if not url_aviso or url_aviso in vistos:
                        continue
                    vistos.add(url_aviso)

                    # Intentar extraer info del texto del card
                    texto_card = link.text.strip()
                    lineas = [l.strip() for l in texto_card.split("\n") if l.strip()]

                    titulo = _texto_seguro(link, ["h2", "h3", "[class*='title']", "[class*='titulo']", "[class*='Title']"])
                    if not titulo and lineas:
                        titulo = lineas[0]

                    empresa = _texto_seguro(link, [
                        "[class*='company']", "[class*='empresa']", "[class*='Company']",
                        "[class*='employer']", "span[class*='sc-']",
                    ])
                    if not empresa and len(lineas) > 1:
                        empresa = lineas[1]

                    ubicacion = _texto_seguro(link, [
                        "[class*='location']", "[class*='ubicacion']", "[class*='Location']",
                        "address", "span[class*='loc']",
                    ])

                    fecha = _texto_seguro(link, [
                        "time", "[class*='date']", "[class*='fecha']",
                        "[class*='Date']", "[datetime]",
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

        except Exception as exc:
            if progress_callback:
                progress_callback(None, f"[{fuente} p{pagina}] Error: {str(exc)[:80]}")
            continue  # Intentar la próxima página

    return empleos


def _obtener_descripcion(driver, url_aviso: str) -> Optional[str]:
    es_selecta = "selecta" in url_aviso.lower()
    sleep_inicial = 4.0 if es_selecta else 2.0
    timeout = 20 if es_selecta else 15

    try:
        driver.get(url_aviso)
        _esperar_pagina(driver, timeout=timeout)
        time.sleep(sleep_inicial)

        # Caso iframe (Selecta y algunos avisos externos)
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

        # Selectores de descripción (del más específico al más genérico)
        for selector in [
            "div#ficha-detalle",
            "div#section-detalle",
            "[data-testid='job-description']",
            "[data-testid*='description']",
            "[class*='JobDescription']",
            "[class*='job-description']",
            "[class*='description']",
            "[class*='descripcion']",
            "article section",
            "main article",
            "main section",
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
