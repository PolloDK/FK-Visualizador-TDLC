# src/data_collection/scraping_listado.py

import asyncio
from playwright.async_api import async_playwright
import csv
from datetime import datetime

BASE_URL = "https://www.tdlc.cl/sentencia/"
N_PAGINAS = 21  # puedes ajustar según necesites

def normalizar_fecha(fecha_str):
    try:
        fecha_dt = datetime.strptime(fecha_str.strip(), "%d/%m/%y")
        return fecha_dt.strftime("%Y-%m-%d")
    except Exception:
        return ""

async def extraer_sentencias_de_pagina(page, numero_pagina):
    url = f"{BASE_URL}?tdlc_sede=sentencia&tdlc_tipo_causa=&tdlc_tipo_documento=&tdlc_ano=&tdlc_numero_sentencia=&tdlc_rol_causa=&paged={numero_pagina}"
    await page.goto(url, timeout=60000)
    await page.wait_for_selector("article.tdlc-sentencias", timeout=15000)
    articulos = await page.query_selector_all("article.tdlc-sentencias")

    resultados = []
    for idx, articulo in enumerate(articulos):
        try:
            # Fecha
            fecha_elem = await articulo.query_selector(".jet-listing-dynamic-field__content")
            fecha_raw = await fecha_elem.inner_text() if fecha_elem else ""
            fecha = normalizar_fecha(fecha_raw)

            # Número de sentencia
            h2s = await articulo.query_selector_all("h2")
            numero = ""
            for h2 in h2s:
                a = await h2.query_selector("a")
                if a:
                    href = await a.get_attribute("href")
                    if "numero-de-sentencia" in href:
                        numero = await a.inner_text()
                        break

            # Código
            codigo = ""
            for h2 in h2s:
                if not await h2.query_selector("a"):
                    texto = await h2.inner_text()
                    if texto.strip().startswith("C-"):
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
                "numero_sentencia": numero.strip(),
                "codigo": codigo.strip(),
                "descripcion": descripcion.strip(),
                "url_ficha": url_ficha.strip()
            })
        except Exception as e:
            print(f"[ERROR tarjeta página {numero_pagina}]: {e}")
            continue
    return resultados

async def get_listado_sentencias():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        todas_las_sentencias = []
        for i in range(1, N_PAGINAS + 1):
            print(f"Scrapeando página {i}...")
            resultados = await extraer_sentencias_de_pagina(page, i)
            print(f"Página {i}: {len(resultados)} sentencias extraídas")
            todas_las_sentencias.extend(resultados)

        await browser.close()

        with open("data/sentencias_listado.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["fecha", "numero_sentencia", "codigo", "descripcion", "url_ficha"])
            writer.writeheader()
            writer.writerows(todas_las_sentencias)

        return todas_las_sentencias

if __name__ == "__main__":
    resultados = asyncio.run(get_listado_sentencias())
