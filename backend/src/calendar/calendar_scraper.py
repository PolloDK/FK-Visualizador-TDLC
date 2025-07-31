from playwright.sync_api import sync_playwright
import csv
import time
from datetime import datetime

MESES_SIN_RESULTADOS_LIMITE = 3

def extraer_audiencias_mes(page):
    rows = page.query_selector_all("table#selectable tbody tr")
    data = []

    for row in rows:
        cols = row.query_selector_all("td")
        if not cols or len(cols) < 7:
            continue

        data.append({
            "fecha": cols[0].inner_text().strip(),
            "hora": cols[1].inner_text().strip(),
            "rol": cols[2].inner_text().strip(),
            "caratula": cols[3].inner_text().strip(),
            "tipo_audiencia": cols[4].inner_text().strip(),
            "estado": cols[5].inner_text().strip(),
            "doc_resolucion": cols[6].query_selector("a").get_attribute("href") if cols[6].query_selector("a") else ""
        })

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
        # Esperamos que el componente global del calendario cargue completamente
        page.wait_for_selector("div.controls", timeout=15000)
    except Exception as e:
        page.screenshot(path="error_cargando_calendario.png")
        raise Exception("❌ Calendario no cargó correctamente")

    for i in range(24):
        try:
            mes_actual = page.locator("div.title-month span").first.text_content(timeout=5000).strip().lower()
            anio_actual = page.locator("div.title-year span").first.text_content(timeout=5000).strip()
            print(f"📅 En calendario: {mes_actual} {anio_actual}")

            if mes_actual == mes_nombre_deseado and anio_actual == str(anio_deseado):
                print("✅ Mes y año correctos encontrados.")
                return

            page.click("span.next-month")
            page.wait_for_timeout(1200)

        except Exception as e:
            page.screenshot(path="error_ir_a_mes.png")
            raise Exception(f"❌ Error al intentar navegar al mes: {e}")



def scrape_audiencias_mes(page, mes: int, anio: int):
    print(f"📅 Revisando {mes:02d}-{anio}")
    ir_a_mes(page, mes, anio)

    audiencias_totales = []

    # Detectar páginas
    paginador = page.query_selector("ul.box-pagination-calendar")
    if paginador:
        paginas = paginador.query_selector_all("li > a.page-link")
        total_paginas = len(paginas)
    else:
        total_paginas = 0

    for i in range(total_paginas + 1):  # Página 1 incluida
        print(f"  📄 Página {i + 1}...")
        try:
            page.wait_for_selector("table#selectable tbody tr", timeout=10000)
        except:
            page.screenshot(path=f"error_audiencia_{mes:02d}-{anio}.png")
            print(f"⚠️ No se encontró tabla de audiencias en {mes:02d}-{anio}. Probablemente no hay datos.")
            return []
        time.sleep(1)

        audiencias = extraer_audiencias_mes(page)
        audiencias_totales.extend(audiencias)

        # Ir a la siguiente página
        next_page = page.query_selector(f'ul.box-pagination-calendar li > a.page-link:text-is("{i + 2}")')
        if next_page:
            next_page.click()
            page.wait_for_timeout(1000)

    return audiencias_totales

def scrape_todos_los_meses():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://consultas.tdlc.cl/audiencia")

        hoy = datetime.today()
        mes_actual = hoy.month
        anio_actual = hoy.year
        meses_sin_resultados = 0

        todas = []

        while meses_sin_resultados < MESES_SIN_RESULTADOS_LIMITE:
            audiencias = scrape_audiencias_mes(page, mes_actual, anio_actual)

            if audiencias:
                todas.extend(audiencias)
                print(f"✅ {len(audiencias)} audiencias encontradas en {mes_actual:02d}-{anio_actual}")
                meses_sin_resultados = 0
            else:
                print(f"⚠️ Sin audiencias en {mes_actual:02d}-{anio_actual}")
                meses_sin_resultados += 1

            # Avanzar al siguiente mes
            if mes_actual == 12:
                mes_actual = 1
                anio_actual += 1
            else:
                mes_actual += 1

        browser.close()

        if todas:
            with open("backend/data/calendario_audiencias.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=todas[0].keys())
                writer.writeheader()
                writer.writerows(todas)
            print(f"\n📁 Guardado exitoso: {len(todas)} audiencias en backend/data/calendario_audiencias.csv")
        else:
            print("❌ No se encontró ninguna audiencia.")

if __name__ == "__main__":
    scrape_todos_los_meses()
