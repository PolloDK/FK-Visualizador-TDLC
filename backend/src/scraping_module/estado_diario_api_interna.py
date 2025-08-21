import sys
import os

# Ruta absoluta al directorio raíz del proyecto (FK06-VisualizadorTDLC)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

# Agrega el directorio raíz al path de búsqueda de módulos
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime, timedelta
import pandas as pd
import requests
import pytz
import os
import re
from backend.src.notification_module.email_notifier import enviar_aviso_nuevo_documento, enviar_resumen_diario

# --- CONFIGURACIÓN ---
WAIT = 60_000
BASE = "https://consultas.tdlc.cl"
DETALLE_CSV = "backend/data/historic_data/rol_idcausa_detalle.csv"
ESTADO_DIARIO_TMP_CSV = "backend/data/estado_diario/estado_diario_tmp.csv"

# --- NUEVO: Archivo para guardar el detalle de los trámites de cada expediente del día ---
DETALLE_ESTADO_DIARIO_TMP_CSV = "backend/data/estado_diario/estado_diario_detalle_tmp.csv"

# --- CAMPOS PARA CSV ---
FIELDNAMES = [
    "rol", "idCausa",
    "fecha_primer_tramite",
    "fallo_detectado", "referencia_fallo", "fecha_fallo", "link_fallo",
    "reclamo_detectado", "fecha_reclamo", "link_reclamo"
]

def extraer_tramites_del_dia(page, idCausa: str, rol: str, fecha_estado_diario: str):
    url = f"{BASE}/estadoDiario?idCausa={idCausa}"
    
    try:
        page.goto(url, wait_until="load", timeout=WAIT)
        page.wait_for_load_state("networkidle", timeout=WAIT)
    except TimeoutError:
        print(f"⚠️ Primer intento fallido. Reintentando cargar la página de trámites para {rol}.")
        try:
            page.goto(url, wait_until="load", timeout=WAIT)
            page.wait_for_load_state("networkidle", timeout=WAIT)
        except TimeoutError:
            print(f"❌ Fallo de carga de la página de trámites para {rol} después de 2 intentos.")
            return []

    tramites_del_dia = []
    try:
        rows = page.query_selector_all("table tbody tr")
        if not rows:
            print(f"⚠️ No se encontraron filas en la tabla de trámites para {rol}.")
            return []
    except Exception:
        print(f"⚠️ No se pudo cargar la tabla de trámites para {rol}.")
        return []

    for row in rows:
        try:
            # Extraer fecha primero para filtrar eficientemente
            fecha_elem = row.query_selector("span[data-bind*='formatearFecha(fecha())']")
            fecha_tramite_txt = fecha_elem.inner_text().strip() if fecha_elem else None
            
            # Solo procesamos si la fecha del trámite coincide con la del estado diario
            if not fecha_tramite_txt or fecha_tramite_txt != fecha_estado_diario:
                continue

            # Extracción de datos usando selectores fiables (data-bind)
            tipo_tramite_elem = row.query_selector("span[data-bind*='tipoTramite']")
            referencia_elem = row.query_selector("span[data-bind*='referencia']")
            foja_elem = row.query_selector("span[data-bind*='foja()']")
            
            # Verificar la existencia de elementos de botón/icono para detectar otras columnas
            tiene_descarga = row.query_selector("span[title='Descargar Documento']") is not None
            tiene_detalles = row.query_selector("span[title='Ver Detalles']") is not None
            tiene_firmantes = row.query_selector("span[title='Ver Firmantes']") is not None

            # Extracción del enlace de descarga simulando un clic si el botón existe
            link_url = ""
            if tiene_descarga:
                link_elem = row.query_selector("span[title='Descargar Documento']")
                try:
                    with page.expect_download(timeout=5000) as download_info:
                        page.evaluate("el => el.click()", link_elem)
                    download = download_info.value
                    link_url = download.url
                except TimeoutError:
                    print(f"⚠️ No se pudo obtener el link de descarga para un trámite en {rol}. Timeout.")
                    pass

            tramites_del_dia.append({
                "idCausa": idCausa,
                "rol": rol,
                "TipoTramite": tipo_tramite_elem.inner_text().strip() if tipo_tramite_elem else "",
                "Fecha": fecha_tramite_txt,
                "Referencia": referencia_elem.inner_text().strip() if referencia_elem else "",
                "Foja": foja_elem.inner_text().strip() if foja_elem else "",
                "Link_Descarga": link_url,
                "Tiene_Detalles": tiene_detalles,
                "Tiene_Firmantes": tiene_firmantes
            })

        except Exception as e:
            print(f"⚠️ Error procesando una fila de trámites para el rol {rol}: {e}")
            continue

    return tramites_del_dia

# Define los nombres de las columnas de la tabla de trámites
TRAMITES_FIELDNAMES = [
    "TipoTramite",
    "Fecha",
    "Referencia",
    "Foja",
    "Link_Descarga",
    "Tiene_Detalles",
    "Tiene_Firmantes"
]

def analizar_expediente(page, url) -> list:
    """
    Navega a la URL de un expediente y extrae los detalles de los trámites desde la tabla.
    
    Args:
        page (playwright.sync_api.Page): La instancia de la página de Playwright.
        url (str): La URL del expediente a analizar.

    Returns:
        list: Una lista de diccionarios, donde cada diccionario es un trámite.
    """
    print(f"🌐 Navegando a: {url}")
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"❌ Error al navegar a la URL {url}: {e}")
        return []

    try:
        # Esperar a que la tabla de trámites sea visible. 
        # Es el selector más confiable. Tus imágenes sugieren que la tabla tiene una clase como 'table'
        page.wait_for_selector("table.table-condensed", timeout=30000)
    except Exception as e:
        print(f"⚠️ No se encontró la tabla de trámites en {url}: {e}")
        return []

    tramites = []
    
    # Usar un localizador para encontrar el cuerpo de la tabla y sus filas
    try:
        # El cuerpo de la tabla es <tbody>
        tbody = page.locator("table.table-condensed tbody").first
        rows = tbody.locator("tr")
        
        # Iterar sobre cada fila de la tabla
        for i in range(rows.count()):
            row = rows.nth(i)
            # Extraer el texto de cada celda (td) en la fila
            cells = row.locator("td")
            
            tramite_data = {}
            # Asumimos que el orden de las columnas es consistente
            tramite_data["TipoTramite"] = cells.nth(0).inner_text().strip()
            tramite_data["Fecha"] = cells.nth(1).inner_text().strip()
            tramite_data["Referencia"] = cells.nth(2).inner_text().strip()
            
            # La foja y los links pueden variar. Debes adaptar los índices.
            # Este es un ejemplo basado en un orden común de tablas.
            tramite_data["Foja"] = cells.nth(3).inner_text().strip() if cells.count() > 3 else ""

            # Extraer link de descarga si existe
            link_element = cells.nth(4).locator("a").first
            tramite_data["Link_Descarga"] = link_element.get_attribute("href") if link_element else ""
            
            tramites.append(tramite_data)
    except Exception as e:
        print(f"❌ Error al extraer datos de la tabla en {url}: {e}")
        return []

    return tramites

def set_date_input(page, selector: str, valor_dd_mm_yyyy: str):
    inp = page.locator(selector)
    # Seteamos el value sin teclear (evita Enter) y notificamos al binding
    inp.evaluate(
        "(el, val) => {"
        "  el.value = ''; el.dispatchEvent(new Event('input', {bubbles:true}));"
        "  el.value = val; el.dispatchEvent(new Event('input', {bubbles:true}));"
        "  el.dispatchEvent(new Event('change', {bubbles:true}));"
        "}", 
        valor_dd_mm_yyyy
    )
    # perder foco (algunos datepickers sólo aplican al blur)
    page.locator("body").click(position={"x": 1, "y": 1})

def obtener_estado_diario_por_api_con_playwright(fecha: datetime) -> list:
    """
    Obtiene el estado diario de causas desde la API usando Playwright para simular una
    solicitud de navegador y evitar errores 403.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        data = None

        # Configurar un interceptor de red para capturar la respuesta de la API
        def handle_response(response):
            nonlocal data
            # URL de la API que queremos interceptar.
            if "rest/estadodiario/byrango" in response.url:
                try:
                    # Capturamos la respuesta y la guardamos
                    data = response.json()
                    print("✅ Respuesta de la API interceptada exitosamente.")
                except Exception as e:
                    print(f"❌ Error al decodificar la respuesta JSON: {e}")

        page.on("response", handle_response)
        
        # Necesitamos que la página cargue para que la llamada a la API se realice automáticamente
        # Se asume que la llamada a la API ocurre al cargar la página principal del estado diario
        url_principal = "https://consultas.tdlc.cl/tdlc-web/estado-diario/lista-estado-diario"
        print(f"🌐 Navegando a {url_principal} para disparar la llamada a la API...")
        
        try:
            page.goto(url_principal, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"❌ No se pudo cargar la página principal: {e}")
            browser.close()
            return []

        browser.close()
        return data if data else []

class EstadoDiarioScraper:
    def __init__(self, fecha_personalizada=None):
        self.url = "https://consultas.tdlc.cl/estadoDiario"
        self.api_base = "https://consultas.tdlc.cl/rest/causa/byestadodiario/"
        self.link_base = "https://consultas.tdlc.cl/estadoDiario?idCausa="
        self.resultados = []
        self.estado_diario_id = None
        self.fecha = fecha_personalizada # formato: "dd-mm-yyyy"
        self.todos_los_tramites = []
   
    def extraer_estado_diario(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto(self.url, timeout=60000)

            if self.fecha:
                try:
                    fecha_inicio_dt = datetime.strptime(self.fecha, "%d-%m-%Y")
                    fecha_fin_dt = fecha_inicio_dt + timedelta(days=1)
                    fecha_fin = fecha_fin_dt.strftime("%d-%m-%Y")

                    print(f"📅 Seleccionando rango: {self.fecha} → {fecha_fin}")

                    set_date_input(page, "#datetimepicker1 input", self.fecha)
                    set_date_input(page, "#datetimepicker2 input", fecha_fin)

                    buscar_btn = page.locator("form[role='form'] button")
                    buscar_btn.click()

                    page.wait_for_load_state("networkidle", timeout=15000)
                    page.wait_for_selector("tbody[data-bind='foreach: estadoDiarios()'] tr", timeout=15000)

                except Exception as e:
                    print(f"❌ Error seleccionando fechas o cargando causas: {e}")
                    return pd.DataFrame()

            def on_request(request):
                if "byestadodiario" in request.url:
                    match = re.search(r"byestadodiario/(\d+)", request.url)
                    if match:
                        self.estado_diario_id = match.group(1)
                        print(f"📥 Interceptado estado diario ID: {self.estado_diario_id}")

            page.on("request", on_request)
            try:
                page.wait_for_selector("tbody[data-bind='foreach: estadoDiarios()']")
                fila = page.query_selector("tbody[data-bind='foreach: estadoDiarios()'] tr")
            except TimeoutError:
                fila = None
                print("⚠️ No se encontraron filas de estado diario. Reintentando...")

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
                            page.wait_for_timeout(1000)
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

            # --- NUEVA LÓGICA: Guardar los resultados en un CSV temporal ---
            df_resultados = pd.DataFrame(self.resultados)
            if not df_resultados.empty:
                os.makedirs(os.path.dirname(ESTADO_DIARIO_TMP_CSV), exist_ok=True)
                df_resultados.to_csv(ESTADO_DIARIO_TMP_CSV, index=False, encoding="utf-8-sig")
                print(f"✅ Se guardaron los resultados del estado diario en {ESTADO_DIARIO_TMP_CSV}")
            else:
                print("⚠️ No se encontraron resultados del estado diario para guardar.")

            return df_resultados

    def analizar_nuevos_fallos(self):
        """
        Analiza las causas del estado diario, navega a cada una para extraer los trámites
        y detecta nuevos fallos o eventos relevantes.
        """
        if not os.path.exists(ESTADO_DIARIO_TMP_CSV):
            print("⚠️ No se encontró el archivo de estado diario para analizar.")
            return

        # 1. Cargar el listado de causas del día que ya guardaste
        print("📋 Cargando listado de causas desde el archivo temporal...")
        try:
            df_causas_del_dia = pd.read_csv(ESTADO_DIARIO_TMP_CSV, dtype=str)
        except Exception as e:
            print(f"❌ Error al leer el archivo {ESTADO_DIARIO_TMP_CSV}: {e}")
            return

        # 2. Cargar el archivo de detalle histórico para detectar nuevas causas
        if os.path.exists(DETALLE_CSV):
            df_detalle = pd.read_csv(DETALLE_CSV, dtype=str)
        else:
            df_detalle = pd.DataFrame(columns=FIELDNAMES)

        nuevas_causas_a_agregar = []
        self.todos_los_tramites = []
        tramites_encontrados = 0
        eventos_del_dia = []
        
        # 3. Iniciar Playwright para la navegación y extracción
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 4. Iterar sobre cada causa del estado diario
            for index, row in df_causas_del_dia.iterrows():
                rol = row.get("rol", "")
                link = row.get("link", "")
                
                if not rol or not link:
                    print(f"⚠️ Fila con datos incompletos, omitiendo. Fila: {row.to_dict()}")
                    continue
                
                print(f"🔎 Analizando expediente {rol}...")
                
                # Detectar si es una nueva causa
                if rol not in df_detalle["rol"].values:
                    print(f"✨ ¡Nueva causa detectada! {rol}")
                    
                    nuevo_registro = {
                        "rol": rol,
                        "idCausa": row.get("idCausa", ""),
                        "fecha_primer_tramite": "", 
                        "fallo_detectado": False,
                        "referencia_fallo": "",
                        "fecha_fallo": "",
                        "link_fallo": "",
                        "reclamo_detectado": False,
                        "fecha_reclamo": "",
                        "link_reclamo": ""
                    }
                    nuevas_causas_a_agregar.append(nuevo_registro)
                    eventos_del_dia.append({
                        "tipo": "Nueva Causa",
                        "rol": rol,
                        "descripcion": row.get("descripcion", "")
                    })
                
                # 5. Extraer los trámites del expediente usando la función de scraping
                tramites_del_expediente = analizar_expediente(page, link)
                
                # 6. Procesar los trámites encontrados
                for tramite in tramites_del_expediente:
                    # Añade el rol y el idCausa para la consistencia de los datos
                    tramite["rol"] = rol
                    tramite["idCausa"] = row.get("idCausa", "")
                    self.todos_los_tramites.append(tramite)
                    tramites_encontrados += 1
                    
                    # --- Aquí va tu lógica para detectar fallos, reclamos, etc. ---
                    referencia = tramite.get("Referencia", "").lower()
                    if "sentencia" in referencia:
                        print(f"🚨 ¡Fallo detectado! Rol: {rol}")
                        # Lógica para actualizar el registro del fallo
                    if "reclamación" in referencia:
                        print(f"🚨 ¡Reclamación detectada! Rol: {rol}")
                        # Lógica para actualizar el registro del reclamo
                
            browser.close()

        # 7. Guardar los datos procesados y enviar el resumen
        if nuevas_causas_a_agregar:
            df_nuevos = pd.DataFrame(nuevas_causas_a_agregar)
            df_detalle = pd.concat([df_detalle, df_nuevos], ignore_index=True)
            df_detalle.to_csv(DETALLE_CSV, index=False, encoding="utf-8-sig")
            print(f"✅ Se guardaron los cambios en {DETALLE_CSV}.")

        if self.todos_los_tramites:
            df_tramites = pd.DataFrame(self.todos_los_tramites)
            os.makedirs(os.path.dirname(DETALLE_ESTADO_DIARIO_TMP_CSV), exist_ok=True)
            df_tramites.to_csv(DETALLE_ESTADO_DIARIO_TMP_CSV, index=False, encoding="utf-8-sig")
            print(f"✅ Se guardó el detalle de los trámites en {DETALLE_ESTADO_DIARIO_TMP_CSV}")
        else:
            print("ℹ️ No se encontraron trámites para guardar en el detalle.")

        listado_tramites = self.todos_los_tramites
        
        print(f"\n--- Resumen del Día ---")
        print(f"Total de expedientes analizados: {len(df_causas_del_dia)}")
        print(f"Total de trámites encontrados: {tramites_encontrados}")
        print(f"Total de eventos importantes detectados: {len(eventos_del_dia)}")
        print(f"-----------------------\n")
        
        enviar_resumen_diario(
            fecha=self.fecha,
            total_tramites=tramites_encontrados,
            eventos_del_dia=eventos_del_dia,
            listado_tramites=listado_tramites
        )        
        
if __name__ == "__main__":
    from datetime import datetime, timedelta

    scraper = EstadoDiarioScraper()
    scraper.extraer_estado_diario()
    scraper.analizar_nuevos_fallos()