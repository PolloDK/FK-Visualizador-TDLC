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
from backend.src.notification_module.email_notifier import enviar_correo_resumen_diario, enviar_resumen_diario

# --- CONFIGURACIÓN ---
WAIT = 30_000
BASE = "https://consultas.tdlc.cl"
DETALLE_CSV = "backend/data/historic_data/rol_idcausa_detalle_actualizado.csv"
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
        print(f"⚠️ Primer intento fallido. Reintentando cargar {rol}")
        try:
            page.goto(url, wait_until="load", timeout=WAIT)
            page.wait_for_load_state("networkidle", timeout=WAIT)
        except TimeoutError:
            print(f"❌ Fallo al cargar trámites para {rol}")
            return []

    tramites_todos_los_cuadernos = []

    try:
        select = page.query_selector("select[name='selectCuaderno']")
        opciones = select.query_selector_all("option") if select else []
        if not opciones:
            print(f"⚠️ No se encontraron opciones de cuadernos en {rol}")
            return []

        for opcion in opciones:
            nombre_cuaderno = opcion.inner_text().strip()

            # Hacer clic en el select
            select = page.locator("div:has-text('Cuaderno') select[name='selectCuaderno']").first
            select.click()

            # Clic en la opción con ese texto
            page.get_by_role("option", name=nombre_cuaderno).click()

            # Esperar a que se actualice la tabla
            page.wait_for_timeout(1500)
            page.wait_for_load_state("networkidle", timeout=WAIT)

            page.wait_for_timeout(1000)  # Esperar a que cambie el contenido
            page.wait_for_load_state("networkidle", timeout=WAIT)

            # Volver a capturar filas de tabla
            rows = page.query_selector_all("table tbody tr")

            for row in rows:
                try:
                    fecha_elem = row.query_selector("span[data-bind*='formatearFecha(fecha())']")
                    fecha_tramite_txt = fecha_elem.inner_text().strip() if fecha_elem else None

                    if not fecha_tramite_txt or fecha_tramite_txt != fecha_estado_diario:
                        continue

                    tipo_tramite_elem = row.query_selector("span[data-bind*='tipoTramite']")
                    referencia_elem = row.query_selector("span[data-bind*='referencia']")
                    foja_elem = row.query_selector("span[data-bind*='foja()']")

                    tiene_descarga = row.query_selector("span[title='Descargar Documento']") is not None
                    tiene_detalles = row.query_selector("span[title='Ver Detalles']") is not None
                    tiene_firmantes = row.query_selector("span[title='Ver Firmantes']") is not None

                    link_url = ""
                    if tiene_descarga:
                        try:
                            link_elem = row.query_selector("span[title='Descargar Documento']")
                            with page.expect_download(timeout=5000) as download_info:
                                page.evaluate("el => el.click()", link_elem)
                            download = download_info.value
                            link_url = download.url
                        except TimeoutError:
                            print(f"⚠️ Link descarga fallido para trámite en {rol} - cuaderno {value}")

                    tramite = {
                        "idCausa": idCausa,
                        "rol": rol,
                        "TipoTramite": tipo_tramite_elem.inner_text().strip() if tipo_tramite_elem else "",
                        "Fecha": fecha_tramite_txt,
                        "Referencia": referencia_elem.inner_text().strip() if referencia_elem else "",
                        "Foja": foja_elem.inner_text().strip() if foja_elem else "",
                        "Link_Descarga": link_url,
                        "Tiene_Detalles": tiene_detalles,
                        "Tiene_Firmantes": tiene_firmantes,
                        "Cuaderno": opcion.inner_text().strip()
                    }

                    tramites_todos_los_cuadernos.append(tramite)

                except Exception as e:
                    print(f"⚠️ Error procesando fila en {rol} cuaderno {value}: {e}")
                    continue

    except Exception as e:
        print(f"❌ Error al intentar recorrer cuadernos de {rol}: {e}")
        return []

    return tramites_todos_los_cuadernos

def analizar_expediente(page, idCausa: str):
    url = f"{BASE}/estadoDiario?idCausa={idCausa}"
    page.goto(url, wait_until="load")
    page.wait_for_load_state("networkidle", timeout=WAIT)

    try:
        rows = page.query_selector_all("table tbody tr")
        if not rows:
            print("⚠️ No se pudo cargar correctamente la tabla del expediente.")
            return None
    except Exception:
        print("⚠️ Timeout esperando la tabla de trámites.")
        return None

    primer_fecha = None
    fallo_detectado = False
    fallo_fecha = None
    referencia_fallo = None
    fallo_link = None
    reclamo_detectado = False
    reclamo_fecha = None
    reclamo_link = None

    keywords_fallo = [
        "sentencia n°", "resolución n°", "informe n°", "acuerdo extrajudicial",
        "ae", "proposición", "proposición normativa", "instrucción de carácter general",
        "certificado agrega bases de conciliación"
    ]

    keywords_exclusion = [
        "escrito", "respuesta", "oficio", "ord. n°", "actuación"
    ]

    for row in rows:
        texto_fila_completo = row.inner_text().strip()
        texto_fila = texto_fila_completo.lower()

        try:
            fecha_txt = row.query_selector_all("td")[-4].inner_text().strip()
            fecha = datetime.strptime(fecha_txt, "%d-%m-%Y")
            if not primer_fecha or fecha < primer_fecha:
                primer_fecha = fecha
        except Exception:
            fecha = None

        if not fallo_detectado:
            contiene_fallo = any(kw in texto_fila for kw in keywords_fallo)
            contiene_excluidos = any(ex in texto_fila for ex in keywords_exclusion)

            if contiene_fallo and not contiene_excluidos and fecha:
                fallo_detectado = True
                fallo_fecha = fecha
                referencia_fallo = texto_fila_completo.replace("\n", " ").strip()

                try:
                    span = row.query_selector("span[title='Descargar Documento']")
                    if span:
                        page.evaluate("span => span.click()", span)
                        with page.expect_download(timeout=5000) as download_info:
                            download = download_info.value
                            fallo_link = download.url
                except:
                    pass

        if fallo_detectado and fecha and fecha > fallo_fecha:
            if "elévese los autos" in texto_fila:
                reclamo_detectado = True
                reclamo_fecha = fecha
                try:
                    span = row.query_selector("span[title='Descargar Documento']")
                    if span:
                        page.evaluate("span => span.click()", span)
                        with page.expect_download(timeout=5000) as download_info:
                            download = download_info.value
                            reclamo_link = download.url
                except:
                    pass

    return {
        "fecha_primer_tramite": primer_fecha.strftime("%Y-%m-%d") if primer_fecha else "",
        "fallo_detectado": fallo_detectado,
        "referencia_fallo": referencia_fallo or "",
        "fecha_fallo": fallo_fecha.strftime("%Y-%m-%d") if fallo_fecha else "",
        "link_fallo": fallo_link or "",
        "reclamo_detectado": reclamo_detectado,
        "fecha_reclamo": reclamo_fecha.strftime("%Y-%m-%d") if reclamo_fecha else "",
        "link_reclamo": reclamo_link or ""
    }

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
            browser = p.chromium.launch(headless=True)
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

            df_resultados = pd.DataFrame(self.resultados)
            if not df_resultados.empty:
                os.makedirs(os.path.dirname(ESTADO_DIARIO_TMP_CSV), exist_ok=True)
                df_resultados.to_csv(ESTADO_DIARIO_TMP_CSV, index=False, encoding="utf-8-sig")
                print(f"✅ Se guardaron los resultados del estado diario en {ESTADO_DIARIO_TMP_CSV}")
            else:
                print("⚠️ No se encontraron resultados del estado diario para guardar.")

            return df_resultados

    def analizar_nuevos_fallos(self):
        if not self.resultados:
            print("⚠️ No hay causas a analizar.")
            return

        # Cargar el archivo de detalle histórico
        if os.path.exists(DETALLE_CSV):
            df_detalle = pd.read_csv(DETALLE_CSV, dtype=str)
        else:
            df_detalle = pd.DataFrame(columns=FIELDNAMES)
        
        nuevas_causas_a_agregar = []
        eventos_del_dia = []
        actualizado_df_detalle = False

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            tramites_encontrados = 0
            for causa in self.resultados:
                rol = causa["rol"]
                idCausa = causa["link"].split("idCausa=")[-1]

                # --- Notificación de NUEVA CAUSA ---
                if rol not in df_detalle["rol"].values:
                    print(f"✨ ¡Nueva causa detectada! {rol}")
                    
                    detalle_expediente = analizar_expediente(page, idCausa)
                    fecha_primer_tramite = detalle_expediente.get("fecha_primer_tramite", "")
                    tipo_causa = causa.get("descripcion", "")

                    nuevo_registro = {
                        "rol": rol,
                        "idCausa": idCausa,
                        "fecha_primer_tramite": fecha_primer_tramite,
                        "fallo_detectado": False,
                        "referencia_fallo": "",
                        "fecha_fallo": "",
                        "link_fallo": "",
                        "reclamo_detectado": False,
                        "fecha_reclamo": "",
                        "link_reclamo": ""
                    }
                    #nuevas_causas_a_agregar.append(nuevo_registro)
                    evento = {
                        "tipo": "nueva_causa",
                        "descripcion": f"Se ha publicado una nueva causa. Tipo: {tipo_causa}",
                        "link": f"{self.link_base}{idCausa}",
                        "fecha": fecha_primer_tramite,
                        "rol": rol,
                        "id_causa": idCausa
                    }
                    eventos_del_dia.append(evento)

                print(f"🔎 Analizando expediente {rol} ({idCausa})...")
                
                # Obtener los trámites del día y guardarlos en la lista general
                try:
                    tramites = extraer_tramites_del_dia(page, idCausa, rol, self.fecha)
                    self.todos_los_tramites.extend(tramites)
                    print(f"✅ Se encontraron {len(tramites)} trámites para este expediente.")
                    tramites_encontrados += len(tramites)
                except Exception as e:
                    print(f"❌ Error al intentar extraer trámites de {rol} ({idCausa}): {e}")
                    continue

                for tramite in tramites:
                    referencia = tramite.get("Referencia", "").lower()
                    
                    # --- Notificación de CONCILIACIÓN ---
                    if "conciliación" in referencia or "bases de conciliación" in referencia:
                        print(f"⚖️ ¡Nueva conciliación detectada en el expediente {rol}!")
                        
                        indice = df_detalle[(df_detalle["rol"] == rol) & (df_detalle["idCausa"] == idCausa)].index
                        
                        if not indice.empty:
                            #df_detalle.loc[indice, "fallo_detectado"] = True
                            #df_detalle.loc[indice, "fecha_fallo"] = tramite.get("Fecha", "")
                            #df_detalle.loc[indice, "referencia_fallo"] = "Conciliación"
                            #actualizado_df_detalle = True
                            #print(f"✅ Se actualizó el registro de {rol} en {DETALLE_CSV}.")
                            
                            evento = {
                                "tipo": "conciliacion",
                                "descripcion": "Nueva conciliación detectada.",
                                "link": f"{self.link_base}{idCausa}",
                                "fecha": tramite.get("Fecha", ""),
                                "rol": rol,
                                "id_causa": idCausa
                            }
                            eventos_del_dia.append(evento)
                        else:
                            print(f"⚠️ No se encontró el expediente {rol} ({idCausa}) en la base de datos para actualizar.")
                    
                    # --- Notificación de RECLAMACIÓN ---
                    keywords_reclamacion = [
                        "eleva autos", "certificado eleva autos", "el\u00e9vese autos",
                        "elevanse los autos", "eleva los autos al tribunal de alzada",
                        "por interpuesta reclamaci\u00f3n", "recurso de reclamaci\u00f3n"
                    ]
                    
                    if any(keyword in referencia for keyword in keywords_reclamacion):
                        print(f"🚨 ¡Reclamación elevada al CS detectada en el expediente {rol}!")
                        
                        indice = df_detalle[(df_detalle["rol"] == rol) & (df_detalle["idCausa"] == idCausa)].index
                        
                        if not indice.empty:
                            #df_detalle.loc[indice, "reclamo_detectado"] = True
                            #df_detalle.loc[indice, "fecha_reclamo"] = tramite.get("Fecha", "")
                            #df_detalle.loc[indice, "link_reclamo"] = tramite.get("Link_Descarga", "")
                            #actualizado_df_detalle = True
                            #print(f"✅ Se actualizó el registro de {rol} con datos de reclamación en {DETALLE_CSV}.")

                            evento = {
                                "tipo": "reclamacion",
                                "descripcion": "Reclamación elevada al CS.",
                                "link": f"{self.link_base}{idCausa}",
                                "fecha": tramite.get("Fecha", ""),
                                "rol": rol,
                                "id_causa": idCausa
                            }
                            eventos_del_dia.append(evento)
                        else:
                            print(f"⚠️ No se encontró el expediente {rol} ({idCausa}) en la base de datos para actualizar la reclamación.")

                # --- Notificación de NUEVO FALLO (Fallo no conciliación) ---
                detalle = analizar_expediente(page, idCausa)
                if not detalle or not detalle["fallo_detectado"]:
                    continue

                duplicado_exacto = (
                    (df_detalle["rol"] == rol) &
                    (df_detalle["idCausa"] == idCausa) &
                    (df_detalle["fecha_fallo"] == detalle["fecha_fallo"])
                ).any()

                es_fallo_del_dia = detalle["fecha_fallo"] == self.fecha
                es_conciliacion = "conciliación" in detalle.get("referencia_fallo", "").lower()

                if not duplicado_exacto and es_fallo_del_dia and not es_conciliacion:
                    print(f"⚖️ ¡Nuevo fallo del día detectado! {detalle['referencia_fallo']}")
                    
                    #df_detalle = pd.concat([df_detalle, pd.DataFrame([{
                    #    "rol": rol,
                    #    "idCausa": idCausa,
                    #    **detalle
                    #}])], ignore_index=True)
                    #actualizado_df_detalle = True
                    
                    evento = {
                        "tipo": "fallo",
                        "descripcion": detalle['referencia_fallo'],
                        "link": f"{self.link_base}{idCausa}",
                        "fecha": detalle["fecha_fallo"],
                        "rol": rol,
                        "id_causa": idCausa
                    }
                    eventos_del_dia.append(evento)
                    
            browser.close()
            
            # --- Guardar datos y resumen ---
            if nuevas_causas_a_agregar:
                df_nuevos = pd.DataFrame(nuevas_causas_a_agregar)
                df_detalle = pd.concat([df_detalle, df_nuevos], ignore_index=True)
                actualizado_df_detalle = True
            
            if actualizado_df_detalle:
                df_detalle.to_csv(DETALLE_CSV, index=False, encoding="utf-8-sig")
                print(f"✅ Se guardaron los cambios en {DETALLE_CSV}.")
            
            # Guardar la lista de trámites del día
            if self.todos_los_tramites:
                df_tramites = pd.DataFrame(self.todos_los_tramites)
                os.makedirs(os.path.dirname(DETALLE_ESTADO_DIARIO_TMP_CSV), exist_ok=True)
                df_tramites.to_csv(DETALLE_ESTADO_DIARIO_TMP_CSV, index=False, encoding="utf-8-sig")
                print(f"✅ Se guardó el detalle de los trámites en {DETALLE_ESTADO_DIARIO_TMP_CSV}")
            else:
                print("ℹ️ No se encontraron trámites para guardar en el detalle.")
                
            # --- Cargar listado de trámites desde el archivo CSV para el resumen ---
            listado_tramites = []
            if os.path.exists(DETALLE_ESTADO_DIARIO_TMP_CSV):
                try:
                    df_tramites = pd.read_csv(DETALLE_ESTADO_DIARIO_TMP_CSV, dtype=str)
                    listado_tramites = df_tramites.to_dict('records')
                    print("✅ Trámites del día cargados desde el archivo CSV.")
                except Exception as e:
                    print(f"❌ Error al cargar trámites desde {DETALLE_ESTADO_DIARIO_TMP_CSV}: {e}")
            else:
                print("⚠️ No se encontró el archivo de trámites del día para el resumen.")
                
            print(f"\n--- Resumen del Día ---")
            print(f"Total de expedientes analizados: {len(self.resultados)}")
            print(f"Total de trámites encontrados: {tramites_encontrados}")
            print(f"Total de eventos importantes detectados: {len(eventos_del_dia)}")
            print(f"-----------------------\n")
            
            # --- Llamada a la función de resumen diario ---
            enviar_resumen_diario(
                fecha=self.fecha,
                total_tramites=tramites_encontrados,
                eventos_del_dia=eventos_del_dia,
                listado_tramites=listado_tramites
            )
            
            enviar_correo_resumen_diario(
                fecha=self.fecha,
                total_tramites=tramites_encontrados,
                listado_tramites=listado_tramites
            )
            
        # Guardar la lista de trámites del día
        if self.todos_los_tramites:
            df_tramites = pd.DataFrame(self.todos_los_tramites)
            os.makedirs(os.path.dirname(DETALLE_ESTADO_DIARIO_TMP_CSV), exist_ok=True)
            df_tramites.to_csv(DETALLE_ESTADO_DIARIO_TMP_CSV, index=False, encoding="utf-8-sig")
            print(f"✅ Se guardó el detalle de los trámites en {DETALLE_ESTADO_DIARIO_TMP_CSV}")
        else:
            print("ℹ️ No se encontraron trámites para guardar en el detalle.")       
                 
if __name__ == "__main__":
    from datetime import datetime, timedelta

    scraper = EstadoDiarioScraper()
    scraper.extraer_estado_diario()
    scraper.analizar_nuevos_fallos()