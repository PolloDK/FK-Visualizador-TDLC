from playwright.sync_api import sync_playwright
import csv
import time
from datetime import datetime
import os
import pandas as pd

class CalendarioScraper:
    def __init__(self, url="https://consultas.tdlc.cl/audiencia", output_path="backend/data/calendario_audiencias.csv", limite_meses_sin_datos=3):
        self.url = url
        self.output_path = output_path
        self.limite_meses_sin_datos = limite_meses_sin_datos
        self.meses_sin_resultados = 0
        self.todas_audiencias = []
        self.meses_scrapeados = self.obtener_meses_scrapeados()

    def obtener_meses_scrapeados(self):
        if not os.path.exists(self.output_path):
            return set()
        df = pd.read_csv(self.output_path)
        if "fecha" not in df.columns:
            return set()
        df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
        return set(df.dropna(subset=["fecha"])["fecha"].dt.strftime("%Y-%m").unique())

    def iniciar_navegador(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()
        self.page.goto(self.url)
        print("🌐 Navegador iniciado y página cargada")

    def cerrar_navegador(self):
        self.browser.close()
        self.playwright.stop()
        print("🔒 Navegador cerrado correctamente")

    def extraer_audiencias_mes(self):
        rows = self.page.query_selector_all("table#selectable tbody tr")
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

    def ir_a_mes(self, mes_deseado, anio_deseado):
        MES_NUM_A_NOMBRE = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        mes_nombre = MES_NUM_A_NOMBRE[mes_deseado].lower()
        print(f"\n🔄 Navegando al mes: {mes_nombre} {anio_deseado}")

        for _ in range(24):
            mes_actual = self.page.locator("div.title-month span").first.text_content(timeout=5000).strip().lower()
            anio_actual = self.page.locator("div.title-year span").first.text_content(timeout=5000).strip()

            if mes_actual == mes_nombre and anio_actual == str(anio_deseado):
                print("✅ Mes y año correctos encontrados.")
                return

            self.page.click("span.previous-month")  # Retroceder
            self.page.wait_for_timeout(1200)

    def scrape_mes(self, mes: int, anio: int):
        clave_mes = f"{anio}-{mes:02d}"
        if clave_mes in self.meses_scrapeados:
            print(f"🛑 {clave_mes} ya scrapeado. Saltando.")
            return []

        print(f"\n📅 Iniciando extracción de audiencias para {mes:02d}-{anio}")
        self.ir_a_mes(mes, anio)

        audiencias_totales = []
        paginador = self.page.query_selector("ul.box-pagination-calendar")
        total_paginas = len(paginador.query_selector_all("li > a.page-link")) if paginador else 0

        for i in range(total_paginas + 1):
            print(f"  📄 Página {i + 1}...")
            self.page.wait_for_selector("table#selectable tbody tr", timeout=10000)
            time.sleep(1)
            audiencias = self.extraer_audiencias_mes()
            audiencias_totales.extend(audiencias)

            next_page = self.page.query_selector(f'ul.box-pagination-calendar li > a.page-link:text-is("{i + 2}")')
            if next_page:
                next_page.click()
                self.page.wait_for_timeout(1000)

        return audiencias_totales

    def guardar_csv(self):
        modo = "a" if os.path.exists(self.output_path) else "w"
        with open(self.output_path, modo, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "fecha", "hora", "rol", "caratula", "tipo_audiencia", "estado", "doc_resolucion"
            ])
            if modo == "w":
                writer.writeheader()
            writer.writerows(self.todas_audiencias)
        print(f"\n💾 {len(self.todas_audiencias)} audiencias agregadas a: {self.output_path}")

    def correr_hacia_atras(self):
        self.iniciar_navegador()
        hoy = datetime.today()
        mes_actual = hoy.month
        anio_actual = hoy.year

        while self.meses_sin_resultados < self.limite_meses_sin_datos:
            audiencias = self.scrape_mes(mes_actual, anio_actual)

            if audiencias:
                self.todas_audiencias.extend(audiencias)
                print(f"✅ {len(audiencias)} audiencias encontradas en {mes_actual:02d}-{anio_actual}")
                self.meses_sin_resultados = 0
            else:
                print(f"⚠️ Sin audiencias en {mes_actual:02d}-{anio_actual}")
                self.meses_sin_resultados += 1

            # Retroceder un mes
            if mes_actual == 1:
                mes_actual = 12
                anio_actual -= 1
            else:
                mes_actual -= 1

        self.guardar_csv()
        self.cerrar_navegador()


if __name__ == "__main__":
    scraper = CalendarioScraper()
    scraper.correr_hacia_atras()
