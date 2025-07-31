import csv
import os
import re
import time
from datetime import datetime
from tqdm import tqdm
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

class ResolucionesTDLC:
    BASE_URL = "https://www.tdlc.cl/?page_id=38816&sort_order=_sfm_orden+desc+num"
    LISTADO_CSV = "backend/data/resoluciones_listado.csv"
    DETALLE_CSV = "backend/data/resoluciones_detalle.csv"
    N_PAGINAS = 8  # ajusta si cambia

    def __init__(self):
        os.makedirs("backend/data", exist_ok=True)

    def obtener_ultimo_numero_resolucion(self):
        if not os.path.exists(self.LISTADO_CSV):
            print("⚠️ No existe el archivo de listado, partimos desde cero")
            return 0
        with open(self.LISTADO_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            numeros = [int(r["numero_resolucion"]) for r in reader if r["numero_resolucion"].isdigit()]
            ultimo = max(numeros) if numeros else 0
            print(f"📌 Último número de resolución registrado: {ultimo}")
            return ultimo

    def normalizar_fecha(self, fecha_str):
        try:
            fecha_dt = datetime.strptime(fecha_str.strip(), "%d/%m/%y")
            return fecha_dt.strftime("%Y-%m-%d")
        except Exception:
            return ""

    def scrapear_listado(self):
        resultados = []
        ultimo = self.obtener_ultimo_numero_resolucion()  # ✅ se mueve aquí
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for i in range(1, self.N_PAGINAS + 1):
                print(f"🔍 Página {i}...")
                url = f"{self.BASE_URL}&sf_paged={i}"
                page.goto(url, timeout=60000)
                page.wait_for_selector("article.tdlc-resoluciones", timeout=15000)
                articulos = page.query_selector_all("article.tdlc-resoluciones")

                for art in articulos:
                    try:
                        fecha_raw = art.query_selector(".jet-listing-dynamic-field__content")
                        fecha = self.normalizar_fecha(fecha_raw.inner_text()) if fecha_raw else ""

                        h2s = art.query_selector_all("h2")
                        numero, codigo, url_ficha = "", "", ""

                        for h2 in h2s:
                            a = h2.query_selector("a")
                            if a:
                                href = a.get_attribute("href") or ""
                                if "numero-de-resolucion" in href:
                                    numero = a.inner_text()
                            else:
                                texto = h2.inner_text()
                                if re.match(r"^(NC|C)-\d{2,3}-\d{2}$", texto.strip(), re.IGNORECASE):
                                    codigo = texto.strip()

                        desc_elem = art.query_selector(".elementor-widget-text-editor")
                        descripcion = desc_elem.inner_text().strip() if desc_elem else ""

                        for h2 in reversed(h2s):
                            a = h2.query_selector("a")
                            if a and "Ver Ficha" in a.inner_text():
                                url_ficha = a.get_attribute("href")
                                break

                        num = int(numero.strip())
                        if num <= ultimo:
                            print(f"🛑 Resolución {num} ya registrada. Deteniendo scraping.")
                            browser.close()
                            return resultados

                        resultados.append({
                            "fecha": fecha,
                            "numero_resolucion": numero.strip(),
                            "codigo": codigo.strip(),
                            "descripcion": descripcion.strip(),
                            "url_ficha": url_ficha.strip()
                        })

                    except Exception as e:
                        print(f"❌ Error tarjeta: {e}")
                        continue

            browser.close()
        return resultados

    def extraer_campos_detalle(self, html):
        soup = BeautifulSoup(html, "html.parser")

        def extraer(titulo):
            seccion = soup.find("h2", string=lambda x: x and x.strip().lower() == titulo.lower())
            if not seccion:
                return ""
            col = seccion.find_parent("div", class_="elementor-column").find_next_sibling("div")
            if not col:
                return ""
            contenido = col.select_one(".jet-listing-dynamic-field__content, .jet-listing-dynamic-terms__link")
            return contenido.get_text(separator=" ", strip=True) if contenido else ""

        fecha = self.normalizar_fecha(extraer("FECHA DE DICTACIÓN:"))
        titulo = soup.find("meta", property="og:title")
        caratula = titulo["content"].strip() if titulo else soup.title.string.strip()

        cs_resultado, cs_link = "", ""
        for bloque in soup.select("div.jet-listing-dynamic-field__content"):
            texto = bloque.get_text(strip=True)
            if "Corte Suprema" in texto or "No se interpusieron recursos" in texto:
                cs_resultado = texto
                link = bloque.find("a")
                if link and link.has_attr("href"):
                    cs_link = link["href"]
                break

        return {
            "fecha_dictacion": fecha,
            "caratula": caratula,
            "rol_causa": extraer("ROL DE CAUSA:"),
            "procedimiento": extraer("PROCEDIMIENTO:"),
            "partes": extraer("PARTES:"),
            "ministros_concuerdan": extraer("MINISTROS Y MINISTRAS QUE CONCURREN AL ACUERDO:"),
            "ministro_redactor": extraer("REDACCIÓN:"),
            "conducta": extraer("CONDUCTA:"),
            "industria": extraer("INDUSTRIA:"),
            "articulo_norma": extraer("ARTÍCULO (NORMA):"),
            "objeto_proceso": extraer("OBJETO DE PROCESO:"),
            "resultado_tdlc": extraer("RESULTADO DEL TDLC:"),
            "voto_en_contra": extraer("VOTO EN CONTRA:"),
            "voto_prevencion": extraer("VOTO PREVENCIÓN:"),
            "resolucion_corte_suprema": cs_resultado,
            "link_resolucion_corte_suprema": cs_link,
        }

    def extraer_detalle_resolucion(self, url):
        print(f"📝 Detalle: {url}")
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
                print(f"❌ Error detalle {url}: {e}")
                return {"url": url}
            finally:
                browser.close()

    def guardar_listado(self, nuevas, modo="w"):
        with open(self.LISTADO_CSV, modo, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["fecha", "numero_resolucion", "codigo", "descripcion", "url_ficha"])
            if modo == "w":
                writer.writeheader()
            writer.writerows(nuevas)

    def guardar_detalles(self, detalles):
        campos = [
            "fecha_dictacion", "caratula", "rol_causa", "procedimiento", "partes", "ministros_concuerdan",
            "ministro_redactor", "conducta", "industria", "articulo_norma", "objeto_proceso",
            "resultado_tdlc", "voto_en_contra", "voto_prevencion", "resolucion_corte_suprema",
            "link_resolucion_corte_suprema", "url"
        ]
        with open(self.DETALLE_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            if not os.path.exists(self.DETALLE_CSV):
                writer.writeheader()
            writer.writerows(detalles)

    def actualizar_si_hay_nuevas(self):
        print("🚀 Iniciando verificación de nuevas resoluciones...")
        ultimo_guardado = self.obtener_ultimo_numero_resolucion()
        listado = self.scrapear_listado()

        nuevas = []
        for r in listado:
            try:
                num = int(r["numero_resolucion"])
                if num > ultimo_guardado:
                    nuevas.append(r)
            except:
                continue

        if not nuevas:
            print("✅ No hay nuevas resoluciones publicadas.")
            return

        print(f"📈 Se detectaron {len(nuevas)} nueva(s) resolución(es) con número mayor a {ultimo_guardado}")
        self.guardar_listado(nuevas, modo="a")
        print("💾 Nuevas resoluciones agregadas al listado.")

        detalles = []
        for r in tqdm(nuevas, desc="📘 Detalles"):
            detalle = self.extraer_detalle_resolucion(r["url_ficha"])
            detalles.append(detalle)

        self.guardar_detalles(detalles)
        print("✅ Detalles guardados con éxito.")



if __name__ == "__main__":
    ResolucionesTDLC().actualizar_si_hay_nuevas()
