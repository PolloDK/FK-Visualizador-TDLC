# archivo: tdlc_estado_diario_scraper.py

from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime, timedelta
import pandas as pd
import requests
import pytz
import re
import os


class EstadoDiarioScraper:
    def __init__(self):
        self.url = "https://consultas.tdlc.cl/estadoDiario"
        self.api_base = "https://consultas.tdlc.cl/rest/causa/byestadodiario/"
        self.link_base = "https://consultas.tdlc.cl/estadoDiario?idCausa="
        self.resultados = []
        self.estado_diario_id = None
        self.fecha = None

    def extraer_estado_diario(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto(self.url, timeout=60000)

            # Interceptar solicitud para capturar ID
            def on_request(request):
                if "byestadodiario" in request.url:
                    match = re.search(r"byestadodiario/(\d+)", request.url)
                    if match:
                        self.estado_diario_id = match.group(1)
                        print(f"📥 Interceptado estado diario ID: {self.estado_diario_id}")

            page.on("request", on_request)

            # Esperar tabla
            page.wait_for_selector("tbody[data-bind='foreach: estadoDiarios()']")

            # Obtener primera fila (última fecha)
            fila = page.query_selector("tbody[data-bind='foreach: estadoDiarios()'] tr")

            if fila:
                columnas = fila.query_selector_all("td")
                if len(columnas) == 4:
                    self.fecha = columnas[0].inner_text().strip()
                    print(f"📅 Procesando fila con fecha: {self.fecha}")

                    try:
                        btn_locator = fila.query_selector("span.glyphicon")
                        if btn_locator:
                            btn_locator.scroll_into_view_if_needed()
                            btn_locator.click()
                            page.wait_for_timeout(1000)  # Esperar que cargue el request
                        else:
                            print(f"⚠️ Botón no encontrado para {self.fecha}")
                            return pd.DataFrame()
                    except Exception as e:
                        print(f"⚠️ No se pudo hacer click en detalle para {self.fecha}: {e}")
                        return pd.DataFrame()

                    try:
                        page.click("button[data-dismiss='modal']")
                    except:
                        pass

            # Consultar API solo si se interceptó un ID
            if self.estado_diario_id:
                try:
                    response = page.request.get(self.api_base + self.estado_diario_id)
                    data = response.json()

                    for causa in data:
                        self.resultados.append({
                            "fecha_estado_diario": self.fecha,
                            "rol": causa.get("rol", "").strip(),
                            "descripcion": causa.get("descripcion", "").strip(),
                            "tramites": causa.get("tramites", 0),
                            "link": self.link_base + str(causa["id"])
                        })

                except Exception as e:
                    print(f"❌ Error al obtener causas para id {self.estado_diario_id}: {e}")

            else:
                print("❌ No se interceptó ningún estado diario.")

            browser.close()
            return pd.DataFrame(self.resultados)

    def extraer_tramites_por_fecha(self, fecha_estado_diario_str, input_csv_path):
        print(f"📡 Consultando API de trámites TDLC para {fecha_estado_diario_str}...")

        # Convertir string "dd-mm-YYYY" a datetime
        tz = pytz.timezone("America/Santiago")
        fecha_dt = datetime.strptime(fecha_estado_diario_str, "%d-%m-%Y").date()
        inicio_dt = tz.localize(datetime.combine(fecha_dt, datetime.min.time()))
        fin_dt = tz.localize(datetime.combine(fecha_dt + timedelta(days=1), datetime.min.time()))

        ts_inicio = int(inicio_dt.timestamp() * 1000)
        ts_fin = int(fin_dt.timestamp() * 1000)

        url = f"https://consultas.tdlc.cl/rest/estadodiario/byrango/{ts_inicio}/{ts_fin}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json"
        }

        print(f"🌐 GET {url}")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"Contenido de respuesta:\n{response.text[:300]}")
            return

        try:
            data = response.json()
        except Exception as e:
            print(f"❌ Error parseando JSON:\n{response.text[:300]}")
            return

        # Leer archivo CSV de causas para obtener idCausa -> rol
        df_causas = pd.read_csv(input_csv_path)
        rol_por_id = dict(zip(df_causas["link"].str.extract(r"idCausa=(\d+)")[0].astype(int), df_causas["rol"]))

        resultados = []

        for estado_diario in data:
            for tramite in estado_diario.get("tramites", []):
                try:
                    if tramite.get("estado", {}).get("name") != "FIRMADO":
                        continue
                    if tramite.get("tipoTramite", {}).get("name") not in {"Resolución", "Acta", "Escrito"}:
                        continue
                    if not tramite.get("documento", {}).get("path"):
                        continue

                    fecha_ingreso = datetime.fromtimestamp(tramite["fechaIngreso"] / 1000, tz)
                    if fecha_ingreso.date() != fecha_dt:
                        continue

                    id_causa = tramite["idCausa"]
                    rol = rol_por_id.get(id_causa, "")

                    resultados.append({
                        "id_causa": id_causa,
                        "rol": rol,
                        "tipo_tramite": tramite["tipoTramite"]["name"],
                        "referencia": tramite.get("referencia", ""),
                        "fecha": fecha_ingreso.strftime("%d-%m-%Y"),
                        "foja": tramite.get("documento", {}).get("fojaTramite", ""),
                        "firmante": f"{tramite.get('funcionario', {}).get('nombres', '')} {tramite.get('funcionario', {}).get('apellidos', '')}".strip(),
                        "archivo_nombre": tramite.get("documento", {}).get("nombre", ""),
                        "documento_path": tramite.get("documento", {}).get("pathFirmado") or tramite.get("documento", {}).get("path", "")
                    })

                except Exception as e:
                    print(f"⚠️ Error procesando trámite: {e}")
                    continue

        if not resultados:
            print("⚠️ No se encontraron trámites válidos para esta fecha.")
            return

        df_resultado = pd.DataFrame(resultados)
        output_path = f"backend/data/estado_diario/tramites_{fecha_estado_diario_str}.csv"
        df_resultado.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ Trámites guardados en {output_path}")
    
if __name__ == "__main__":
    scraper = EstadoDiarioScraper()
    df = scraper.extraer_estado_diario()

    if not df.empty:
        fecha_archivo = scraper.fecha.replace("/", "-")
        output_dir = "backend/data/estado_diario"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"estado_diario_{fecha_archivo}.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ Datos guardados en {output_path}")

        # Llamar a la función de trámites integrada en la clase
        print(f"🚀 Iniciando scraping de trámites para {fecha_archivo}...")
        scraper.extraer_tramites_por_fecha(fecha_archivo, output_path)

    else:
        print("⚠️ No se extrajeron datos.")
