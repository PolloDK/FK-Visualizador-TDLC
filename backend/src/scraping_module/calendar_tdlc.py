# scrape_calendar_forward_append.py
from playwright.sync_api import sync_playwright
import csv, os, time
from datetime import datetime
from dateutil.relativedelta import relativedelta

MESES_SIN_RESULTADOS_LIMITE = 3
URL = "https://consultas.tdlc.cl/audiencia"
CSV_PATH = "backend/data/calendar/calendario_audiencias.csv" 

# ============== Utilidades CSV (append + dedupe) ==============
HEADER = ["fecha","hora","rol","caratula","tipo_audiencia","estado","doc_resolucion"]

def cargar_keys_existentes(csv_path: str) -> set[tuple[str, str, str]]:
    keys = set()
    if not os.path.exists(csv_path):
        return keys
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (
                (r.get("fecha") or "").strip(),
                (r.get("hora") or "").strip(),
                (r.get("rol") or "").strip(),
            )
            if any(key):  # ignora filas vacías
                keys.add(key)
    return keys

def append_mes(csv_path: str, filas: list[dict], keys_existentes: set[tuple[str,str,str]]) -> int:
    """Apendea filas nuevas (dedupe por fecha-hora-rol). Crea header si no existe."""
    if not filas:
        return 0

    nuevos = []
    for r in filas:
        key = ((r.get("fecha") or "").strip(), (r.get("hora") or "").strip(), (r.get("rol") or "").strip())
        if key and key not in keys_existentes:
            nuevos.append({
                "fecha": (r.get("fecha") or "").strip(),
                "hora": (r.get("hora") or "").strip(),
                "rol": (r.get("rol") or "").strip(),
                "caratula": (r.get("caratula") or "").strip(),
                "tipo_audiencia": (r.get("tipo_audiencia") or "").strip(),
                "estado": (r.get("estado") or "").strip(),
                "doc_resolucion": (r.get("doc_resolucion") or "").strip(),
            })
            keys_existentes.add(key)

    if not nuevos:
        print("🟰 Nada nuevo que agregar (todo duplicado).")
        return 0

    first_write = not os.path.exists(csv_path)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        if first_write:
            writer.writeheader()
        writer.writerows(nuevos)
    print(f"💾 Agregadas {len(nuevos)} filas nuevas a {csv_path}")
    return len(nuevos)

# ============== Scraper ==============
def extraer_audiencias_mes(page):
    rows = page.query_selector_all("table#selectable tbody tr")
    data = []
    for row in rows:
        cols = row.query_selector_all("td")
        if not cols or len(cols) < 7:
            continue
        try:
            data.append({
                "fecha": cols[0].inner_text().strip(),
                "hora": cols[1].inner_text().strip(),
                "rol": cols[2].inner_text().strip(),
                "caratula": cols[3].inner_text().strip(),
                "tipo_audiencia": cols[4].inner_text().strip(),
                "estado": cols[5].inner_text().strip(),
                "doc_resolucion": cols[6].query_selector("a").get_attribute("href") if cols[6].query_selector("a") else ""
            })
        except Exception:
            continue
    return data

def ir_a_mes(page, mes_deseado, anio_deseado):
    MES_NUM_A_NOMBRE = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    mes_nombre_deseado = MES_NUM_A_NOMBRE[mes_deseado].lower()
    print(f"🧭 Buscando {mes_nombre_deseado} {anio_deseado}")

    try:
        page.wait_for_selector("div.controls", timeout=15000)
    except Exception:
        page.screenshot(path="error_cargando_calendario.png")
        raise Exception("❌ Calendario no cargó correctamente")

    # Intentos: avanza mes a mes hacia adelante (máx 36 pasos)
    for _ in range(36):
        try:
            mes_actual = page.locator("div.title-month span").first.text_content(timeout=5000).strip().lower()
            anio_actual = page.locator("div.title-year span").first.text_content(timeout=5000).strip()
            print(f"📅 En calendario: {mes_actual} {anio_actual}")
            if mes_actual == mes_nombre_deseado and anio_actual == str(anio_deseado):
                print("✅ Mes y año correctos encontrados.")
                return
            # avanzar un mes
            # OJO: en el sitio real el selector es 'span.next-month'
            page.click("span.next-month")
            page.wait_for_load_state("networkidle")
            time.sleep(0.6)
        except Exception as e:
            page.screenshot(path="error_ir_a_mes.png")
            raise Exception(f"❌ Error al intentar navegar al mes: {e}")
    raise Exception("❌ No se alcanzó el mes solicitado (exceso de pasos).")

def scrape_audiencias_mes(page, mes: int, anio: int):
    print(f"📅 Revisando {mes:02d}-{anio}")
    ir_a_mes(page, mes, anio)

    audiencias_totales = []

    # Detectar paginación (si existe)
    paginador = page.query_selector("ul.box-pagination-calendar")
    if paginador:
        paginas = paginador.query_selector_all("li > a.page-link")
        total_paginas = len(paginas)
    else:
        total_paginas = 0

    for i in range(total_paginas + 1):  # incluye página 1
        print(f"  📄 Página {i + 1}...")
        try:
            # Puede no haber tabla en algunos meses (tratar como vacío)
            if not page.query_selector("table#selectable tbody"):
                print("  ↪️ No hay tabla de audiencias en este mes.")
                return []
            page.wait_for_selector("table#selectable tbody tr", timeout=8000)
        except Exception:
            page.screenshot(path=f"error_audiencia_{mes:02d}-{anio}.png")
            print(f"⚠️ No se encontró tabla de audiencias en {mes:02d}-{anio}.")
            return []

        time.sleep(0.5)
        audiencias = extraer_audiencias_mes(page)
        audiencias_totales.extend(audiencias)

        # Siguiente página por número
        next_page = page.query_selector(f'ul.box-pagination-calendar li > a.page-link:text-is("{i + 2}")')
        if next_page:
            next_page.click()
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)

    return audiencias_totales

def scrape_todos_los_meses_hacia_adelante():
    keys_existentes = cargar_keys_existentes(CSV_PATH)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_load_state("domcontentloaded")

        # Desde el mes actual en adelante
        dt = datetime.today().replace(day=1)
        mes_actual, anio_actual = dt.month, dt.year
        meses_sin_resultados = 0

        pasos = 0  # límite de seguridad opcional
        while meses_sin_resultados < MESES_SIN_RESULTADOS_LIMITE and pasos < 60:
            filas_mes = scrape_audiencias_mes(page, mes_actual, anio_actual)

            if filas_mes:
                # append inmediato (mes a mes) con dedupe
                nuevas = append_mes(CSV_PATH, filas_mes, keys_existentes)
                print(f"✅ {len(filas_mes)} filas encontradas, {nuevas} nuevas agregadas en {mes_actual:02d}-{anio_actual}")
                meses_sin_resultados = 0
            else:
                print(f"⚠️ Sin audiencias en {mes_actual:02d}-{anio_actual}")
                meses_sin_resultados += 1

            # Avanzar al siguiente mes
            dt = dt + relativedelta(months=1)
            mes_actual, anio_actual = dt.month, dt.year
            pasos += 1

        browser.close()

    print("🏁 Proceso finalizado.")

if __name__ == "__main__":
    scrape_todos_los_meses_hacia_adelante()
