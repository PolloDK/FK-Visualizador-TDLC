# src/sentencias_tdlc_actualizador.py

import csv
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from datetime import datetime
from tqdm import tqdm


class SentenciasTDLC:

    BASE_URL = "https://www.tdlc.cl/sentencia/"
    LISTADO_CSV = "backend/data/sentencias_listado.csv"
    DETALLE_CSV = "backend/data/sentencias_detalle.csv"

    def __init__(self):
        os.makedirs("data", exist_ok=True)

    def obtener_ultimo_numero_sentencia(self):
        if not os.path.exists(self.LISTADO_CSV):
            print("⚠️ No existe el archivo de listado, partimos desde cero")
            return 0
        with open(self.LISTADO_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            numeros = [int(r["numero_sentencia"]) for r in reader if r["numero_sentencia"].isdigit()]
            ultimo = max(numeros) if numeros else 0
            print(f"📌 Último número de sentencia registrado: {ultimo}")
            return ultimo

    def scrapear_primera_pagina_listado(self):
        print("🔍 Cargando primera página de sentencias...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.BASE_URL, timeout=60000)
            page.wait_for_selector("article.tdlc-sentencias", timeout=15000)
            articulos = page.query_selector_all("article.tdlc-sentencias")
            resultados = []

            for art in articulos:
                try:
                    fecha_elem = art.query_selector(".jet-listing-dynamic-field__content")
                    fecha = fecha_elem.inner_text().strip() if fecha_elem else ""

                    h2s = art.query_selector_all("h2")
                    numero, codigo, url_ficha = "", "", ""

                    for h2 in h2s:
                        a = h2.query_selector("a")
                        if a:
                            href = a.get_attribute("href")
                            texto = a.inner_text().strip()
                            if "Ver Ficha" in texto:
                                url_ficha = href
                            elif "numero-de-sentencia" in href:
                                numero = texto.strip()
                        else:
                            texto = h2.inner_text().strip()
                            if texto.startswith("C-"):
                                codigo = texto

                    descripcion_elem = art.query_selector(".elementor-widget-text-editor")
                    descripcion = descripcion_elem.inner_text().strip() if descripcion_elem else ""

                    resultados.append({
                        "fecha": fecha,
                        "numero_sentencia": numero,
                        "codigo": codigo,
                        "descripcion": descripcion,
                        "url_ficha": url_ficha
                    })
                except Exception as e:
                    print(f"❌ Error en una tarjeta: {e}")
                    continue

            browser.close()
            print(f"✅ Total sentencias detectadas en la primera página: {len(resultados)}")
            return resultados

    def extraer_campos_detalle(self, html):
        soup = BeautifulSoup(html, "html.parser")

        def extraer(titulo):
            seccion = soup.find("h2", string=lambda x: x and x.strip().lower() == titulo.lower())
            if not seccion:
                return ""
            columna_derecha = seccion.find_parent("div", class_="elementor-column").find_next_sibling("div")
            if not columna_derecha:
                return ""
            contenido = columna_derecha.select_one(".jet-listing-dynamic-field__content, .jet-listing-dynamic-terms__link")
            return contenido.get_text(separator=" ", strip=True) if contenido else ""

        def normalizar_fecha(fecha_raw):
            try:
                partes = fecha_raw.strip().replace(",", "").split()
                meses = {
                    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
                    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
                    "septiembre": "09", "setiembre": "09", "octubre": "10",
                    "noviembre": "11", "diciembre": "12"
                }
                mes = meses[partes[0].lower()]
                dia = partes[1].zfill(2)
                anio = partes[2]
                return f"{anio}-{mes}-{dia}"
            except:
                return fecha_raw

        fecha = normalizar_fecha(extraer("FECHA DE DICTACIÓN:"))
        caratula = soup.find("meta", property="og:title")
        caratula = caratula["content"].strip() if caratula else soup.title.string.strip()

        return {
            "fecha_dictacion": fecha,
            "caratula": caratula,
            "rol_causa": extraer("rol de causa:"),
            "procedimiento": extraer("procedimiento:"),
            "partes": extraer("PARTES:"),
            "ministros_concuerdan": extraer("MINISTROS Y MINISTRAS QUE CONCURREN AL ACUERDO:"),
            "ministro_redactor": extraer("MINISTRO/A REDACTOR/A:"),
            "conducta": extraer("CONDUCTA:"),
            "industria": extraer("INDUSTRIA:"),
            "articulo_norma": extraer("ARTÍCULO (NORMA):"),
            "resumen_controversia": extraer("resumen de controversia:"),
            "resultado_tdlc": extraer("resultado del tdlc:"),
            "voto_en_contra": extraer("voto en contra:"),
            "voto_prevencion": extraer("voto prevención:"),
            "temas_tratados": extraer("temas que trata:")
        }

    def extraer_detalle_sentencia(self, url):
        print(f"📝 Extrayendo detalle de: {url}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, timeout=60000)
                page.wait_for_selector(".elementor-section", timeout=15000)
                time.sleep(1)
                html = page.content()
                data = self.extraer_campos_detalle(html)
                data["url"] = url
                return data
            except Exception as e:
                print(f"❌ Error al extraer detalle: {e}")
                return {"url": url}
            finally:
                browser.close()

    def guardar_sentencias_listado(self, nuevas, modo="a"):
        existe = os.path.exists(self.LISTADO_CSV)
        with open(self.LISTADO_CSV, modo, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["fecha", "numero_sentencia", "codigo", "descripcion", "url_ficha"])
            if not existe or modo == "w":
                writer.writeheader()
            writer.writerows(nuevas)

    def guardar_sentencias_detalle(self, nuevas_detalles):
        existe = os.path.exists(self.DETALLE_CSV)
        with open(self.DETALLE_CSV, "a", newline="", encoding="utf-8") as f:
            campos = [
                "fecha_dictacion", "caratula", "rol_causa", "procedimiento", "partes", "ministros_concuerdan",
                "ministro_redactor", "conducta", "industria", "articulo_norma", "resumen_controversia",
                "resultado_tdlc", "voto_en_contra", "voto_prevencion", "temas_tratados", "url"
            ]
            writer = csv.DictWriter(f, fieldnames=campos)
            if not existe:
                writer.writeheader()
            writer.writerows(nuevas_detalles)

    def actualizar_si_hay_nuevas(self):
        print("🚀 Iniciando verificación de nuevas sentencias...")
        ultimo_guardado = self.obtener_ultimo_numero_sentencia()
        primera_pagina = self.scrapear_primera_pagina_listado()

        nuevas = []
        for sentencia in primera_pagina:
            try:
                numero = int(sentencia["numero_sentencia"])
                if numero > ultimo_guardado:
                    nuevas.append(sentencia)
            except:
                continue

        if not nuevas:
            print("✅ No hay nuevas sentencias publicadas.")
            return

        print(f"📈 Se detectaron {len(nuevas)} nueva(s) sentencia(s) con número mayor a {ultimo_guardado}")
        self.guardar_sentencias_listado(nuevas)
        print("💾 Nuevas sentencias agregadas al listado.")

        detalles = []
        for row in tqdm(nuevas, desc="📘 Detalles"):
            detalle = self.extraer_detalle_sentencia(row["url_ficha"])
            detalles.append(detalle)

        self.guardar_sentencias_detalle(detalles)
        print("✅ Detalles guardados con éxito.")


if __name__ == "__main__":
    SentenciasTDLC().actualizar_si_hay_nuevas()
