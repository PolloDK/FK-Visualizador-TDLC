import asyncio
from playwright.async_api import async_playwright
import csv
from datetime import datetime
import re

# URL base corregida
BASE_URL = "https://www.tdlc.cl/?page_id=38816&sort_order=_sfm_orden+desc+num"
N_PAGINAS = 8  # Puedes ajustar este valor si cambian las páginas

def normalizar_fecha(fecha_str):
    try:
        fecha_dt = datetime.strptime(fecha_str.strip(), "%d/%m/%y")
        return fecha_dt.strftime("%Y-%m-%d")
    except Exception:
        return ""

async def extraer_resoluciones_de_pagina(page, numero_pagina):
    url = f"{BASE_URL}&sf_paged={numero_pagina}"
    print(f"🔍 Scrapeando página {numero_pagina} de resoluciones...")
    await page.goto(url, timeout=60000)
    await page.wait_for_selector("article.tdlc-resoluciones", timeout=15000)
    articulos = await page.query_selector_all("article.tdlc-resoluciones")

    resultados = []
    for idx, articulo in enumerate(articulos):
        try:
            # Fecha
            fecha_elem = await articulo.query_selector(".jet-listing-dynamic-field__content")
            fecha_raw = await fecha_elem.inner_text() if fecha_elem else ""
            fecha = normalizar_fecha(fecha_raw)

            # Número de resolución
            h2s = await articulo.query_selector_all("h2")
            numero = ""
            for h2 in h2s:
                a = await h2.query_selector("a")
                if a:
                    href = await a.get_attribute("href") or ""
                    if "numero-de-resolucion" in href:
                        numero = await a.inner_text()
                        break

            # Código: NC-XXX-YY
            codigo = ""
            for h2 in h2s:
                texto = await h2.inner_text()
                if re.match(r"^(NC|C)-\d{2,3}-\d{2}$", texto.strip(), re.IGNORECASE):
                    codigo = texto.strip()
                    break

            # Descripción
            desc_elem = await articulo.query_selector(".elementor-widget-text-editor")
            descripcion = await desc_elem.inner_text() if desc_elem else ""

            # URL Ficha
            url_ficha = ""
            for h2 in reversed(h2s):
                a = await h2.query_selector("a")
                if a:
                    texto = await a.inner_text()
                    if "Ver Ficha" in texto:
                        url_ficha = await a.get_attribute("href")
                        break

            resultados.append({
                "fecha": fecha,
                "numero_resolucion": numero.strip(),
                "codigo": codigo.strip(),
                "descripcion": descripcion.strip(),
                "url_ficha": url_ficha.strip()
            })
        except Exception as e:
            print(f"[❌ ERROR tarjeta página {numero_pagina}]: {e}")
            continue

    return resultados

async def get_listado_resoluciones():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        todas = []
        for i in range(1, N_PAGINAS + 1):
            resultados = await extraer_resoluciones_de_pagina(page, i)
            print(f"✅ Página {i}: {len(resultados)} resoluciones extraídas")
            todas.extend(resultados)

        await browser.close()

        output_file = "backend/data/resoluciones_listado.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["fecha", "numero_resolucion", "codigo", "descripcion", "url_ficha"])
            writer.writeheader()
            writer.writerows(todas)

        print(f"\n📁 Resoluciones guardadas en: {output_file}")
        return todas

if __name__ == "__main__":
    asyncio.run(get_listado_resoluciones())
