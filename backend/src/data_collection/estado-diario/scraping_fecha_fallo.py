from playwright.sync_api import sync_playwright
from datetime import datetime
import csv
import os
import time

WAIT = 50_000
BASE = "https://consultas.tdlc.cl"
CSV_RESULTADOS = "backend/data/historic_data/rol_idcausa_detalle.csv"
CSV_INPUT = "backend/data/historic_data/rol_idcausa.csv"

FIELDNAMES = [
    "rol", "idCausa",
    "fecha_primer_tramite",
    "fallo_detectado", "referencia_fallo", "fecha_fallo", "link_fallo",
    "reclamo_detectado", "fecha_reclamo", "link_reclamo"
]


def append_detalle_csv(path, nuevos: list[dict]):
    if not nuevos:
        return 0
    first = not os.path.exists(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if first:
            w.writeheader()
        w.writerows(nuevos)
    return len(nuevos)


def leer_csv_rol_idcausa(path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [(row["rol"], row["idcausa"]) for row in reader]


def leer_roles_pendientes():
    todos = leer_csv_rol_idcausa(CSV_INPUT)
    if not os.path.exists(CSV_RESULTADOS):
        return todos

    with open(CSV_RESULTADOS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ya_procesados = set((row["rol"], row["idCausa"]) for row in reader)

    pendientes = [r for r in todos if r not in ya_procesados]
    print(f"🔄 Total pendientes por procesar: {len(pendientes)} de {len(todos)}")
    return pendientes


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
        "escrito", "respuesta", "oficio", "ord. n°", "actuación",
        "acta", "audiencia", "testimonial", "absolución", "posición",
        "no divulgación", "citación", "comparecencia", "traslado", "intervención"
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


def run(headless=True):
    roles = leer_roles_pendientes()
    nuevos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        for i, (rol, idc) in enumerate(roles):
            print(f"\n🔎 {i+1}/{len(roles)} Rol: {rol} - idCausa: {idc}")
            try:
                detalles = analizar_expediente(page, idc)
                if detalles is None:
                    continue

                row = {
                    "rol": rol,
                    "idCausa": idc,
                    **detalles
                }

                print(f"  📅 Primer trámite: {detalles['fecha_primer_tramite']}")
                if detalles["fallo_detectado"]:
                    print(f"  ⚖️ Fallo: {detalles['referencia_fallo']} | Fecha: {detalles['fecha_fallo']}")
                if detalles["reclamo_detectado"]:
                    print(f"  📨 Reclamo detectado: {detalles['fecha_reclamo']}")

                nuevos.append(row)
                time.sleep(0.5)

                if (i + 1) % 10 == 0:
                    total = append_detalle_csv(CSV_RESULTADOS, nuevos)
                    print(f"  💾 Guardado parcial de {total} registros...")
                    nuevos.clear()

            except Exception as e:
                print(f"❌ Error con causa {rol}: {e}")
                continue

        total = append_detalle_csv(CSV_RESULTADOS, nuevos)
        print(f"\n✅ Se guardaron {total} registros en: {CSV_RESULTADOS}")
        browser.close()


if __name__ == "__main__":
    run(headless=False)
