from playwright.sync_api import sync_playwright
import csv
import time
from datetime import datetime

class CalendarioScraper:
    def __init__(self, url="https://consultas.tdlc.cl/audiencia", output_path="backend/data/calendario_audiencias.csv", limite_meses_sin_datos=3):
        self.url = url
        self.output_path = output_path
        self.limite_meses_sin_datos = limite_meses_sin_datos
        self.meses_sin_resultados = 0
        self.todas_audiencias = []

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

        try:
            self.page.wait_for_selector("div.controls", timeout=15000)
        except:
            self.page.screenshot(path="error_cargando_calendario.png")
            raise Exception("❌ No se cargó el calendario")

        for _ in range(24):
            try:
                mes_actual = self.page.locator("div.title-month span").first.text_content(timeout=5000).strip().lower()
                anio_actual = self.page.locator("div.title-year span").first.text_content(timeout=5000).strip()
                print(f"📍 Calendario está en: {mes_actual} {anio_actual}")

                if mes_actual == mes_nombre and anio_actual == str(anio_deseado):
                    print("✅ Mes y año correctos encontrados.")
                    return
                self.page.click("span.next-month")
                self.page.wait_for_timeout(1200)
            except Exception as e:
                self.page.screenshot(path="error_ir_a_mes.png")
                raise Exception(f"❌ Error navegando al mes: {e}")

    def scrape_mes(self, mes: int, anio: int):
        print(f"\n📅 Iniciando extracción de audiencias para {mes:02d}-{anio}")
        self.ir_a_mes(mes, anio)

        audiencias_totales = []
        paginador = self.page.query_selector("ul.box-pagination-calendar")
        total_paginas = len(paginador.query_selector_all("li > a.page-link")) if paginador else 0

        for i in range(total_paginas + 1):
            print(f"  📄 Página {i + 1}...")
            try:
                self.page.wait_for_selector("table#selectable tbody tr", timeout=10000)
            except:
                self.page.screenshot(path=f"error_audiencia_{mes:02d}-{anio}.png")
                print(f"⚠️ Tabla de audiencias no encontrada en {mes:02d}-{anio}. Probablemente no hay datos.")
                return []

            time.sleep(1)
            audiencias = self.extraer_audiencias_mes()
            audiencias_totales.extend(audiencias)

            next_page = self.page.query_selector(f'ul.box-pagination-calendar li > a.page-link:text-is("{i + 2}")')
            if next_page:
                next_page.click()
                self.page.wait_for_timeout(1000)

        return audiencias_totales

    def guardar_csv(self):
        if self.todas_audiencias:
            with open(self.output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.todas_audiencias[0].keys())
                writer.writeheader()
                writer.writerows(self.todas_audiencias)
            print(f"\n💾 {len(self.todas_audiencias)} audiencias guardadas en: {self.output_path}")
        else:
            print("❌ No se encontró ninguna audiencia para guardar.")

    def correr(self):
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

            # Avanzar al siguiente mes
            if mes_actual == 12:
                mes_actual = 1
                anio_actual += 1
            else:
                mes_actual += 1

        self.guardar_csv()
        self.cerrar_navegador()

if __name__ == "__main__":
    scraper = CalendarioScraper()
    scraper.correr()
