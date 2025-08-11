# src/data_collection/03-informes/scraping_listado.py

import asyncio
from playwright.async_api import async_playwright
import csv
from datetime import datetime

BASE_URL = "https://www.tdlc.cl/informes-leyes-especiales/"
N_PAGINAS = 4


def normalizar_fecha(fecha_raw):
    try:
        fecha_dt = datetime.strptime(fecha_raw.strip(), "%d/%m/%Y")
        return fecha_dt.strftime("%Y-%m-%d")
    except:
        return fecha_raw


async def extraer_informes_de_pagina(page, numero_pagina):
    url = f"{BASE_URL}?_page={numero_pagina}&sort_order=_sfm_orden%20desc%20num"
    await page.goto(url, timeout=60000)
    await page.wait_for_selector("article.tdlc-informes", timeout=15000)

    articulos = await page.query_selector_all("article.tdlc-informes")
    resultados = []

    for art in articulos:
        try:
            h2s = await art.query_selector_all("h2")
            codigo = ""
            url_ficha = ""

            for h2 in h2s:
                a = await h2.query_selector("a")
                if a:
                    texto = (await a.inner_text()).strip()
                    href = await a.get_attribute("href")
                    if texto.startswith("NC"):
                        codigo = texto
                    if "Ver Ficha" in texto:
                        url_ficha = href

            desc_elem = await art.query_selector(".elementor-widget-text-editor")
            descripcion = (await desc_elem.inner_text()).strip() if desc_elem else ""

            fecha_elem = await art.query_selector(".jet-listing-dynamic-field__content")
            fecha_raw = await fecha_elem.inner_text() if fecha_elem else ""
            fecha = normalizar_fecha(fecha_raw)

            resultados.append({
                "fecha": fecha,
                "numero_sentencia": "",
                "codigo": codigo,
                "descripcion": descripcion,
                "url_ficha": url_ficha
            })
        except Exception as e:
            print(f"[⚠️ Error al procesar tarjeta en página {numero_pagina}]: {e}")
            continue

    return resultados


async def get_listado_informes():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        todos = []
        for i in range(1, N_PAGINAS + 1):
            print(f"🔍 Scrapeando página {i}...")
            resultados = await extraer_informes_de_pagina(page, i)
            print(f"📄 Página {i}: {len(resultados)} informes encontrados.")
            todos.extend(resultados)

        await browser.close()

        with open("data/informes_listado.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["fecha", "numero_sentencia", "codigo", "descripcion", "url_ficha"])
            writer.writeheader()
            writer.writerows(todos)

        print("✅ Archivo guardado como data/informes_listado.csv")
        return todos


if __name__ == "__main__":
    asyncio.run(get_listado_informes())
