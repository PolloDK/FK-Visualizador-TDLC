from playwright.sync_api import sync_playwright
import csv
import time
import re
import argparse

# Lista fija de tipos de causa
TIPOS_CAUSA = [
    "Contencioso",
    "No Contencioso",
    "Instrucción de Carácter General",
    "Normas Técnicas",
    "Consulta Normativa",
    "Recomendación Normativa",
    "Autorizaciones 39, F)",
    "Avenimientos",
    "Proposición Normativa",
    "Acuerdos Extrajudiciales",
]

def run_scraper(output_file, headless=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        print("🌐 Cargando página principal...")
        page.goto("https://www.tdlc.cl")
        page.click("a[href='https://consultas.tdlc.cl/search?proc=3']")
        page.wait_for_url("https://consultas.tdlc.cl/search?proc=3")

        resultados = []

        for tipo in TIPOS_CAUSA:
            print(f"\n🔍 Tipo: {tipo}")

            try:
                page.select_option("select#tipo", label=tipo)
                page.click("button[type='submit']")
                page.wait_for_selector("td[data-bind='text: rolCausa']", timeout=8000)
                time.sleep(1.5)
            except Exception as e:
                print(f"⚠️ No se encontraron resultados para {tipo}: {e}")
                continue

            filas = page.query_selector_all("table tbody tr")
            print(f"   → {len(filas)} filas encontradas")

            for idx, fila in enumerate(filas):
                try:
                    rol = fila.query_selector("td[data-bind='text: rolCausa']").inner_text().strip()
                    fecha = fila.query_selector("td[data-bind='text: fechaIngreso']").inner_text().strip()
                    descripcion = fila.query_selector("td[data-bind='text: descripcion']").inner_text().strip()
                    procedimiento = fila.query_selector("td[data-bind='text: procedimiento']").inner_text().strip()

                    # Simula click para capturar popup con URL
                    with page.expect_popup() as popup_info:
                        btn = fila.query_selector("span.glyphicon-new-window")
                        btn.click()
                    popup = popup_info.value
                    popup_url = popup.url
                    popup.close()

                    match = re.search(r"idCausa=(\d+)", popup_url)
                    id_causa = match.group(1) if match else None
                    link = popup_url if id_causa else None

                    resultados.append({
                        "tipo": tipo,
                        "rol": rol,
                        "fecha_ingreso": fecha,
                        "descripcion": descripcion,
                        "procedimiento": procedimiento,
                        "idcausa": id_causa,
                        "link": link,
                    })

                    print(f"✅ {idx+1}/{len(filas)} {rol} - {id_causa}")

                except Exception as e:
                    print(f"⚠️ Error en fila {idx+1}: {e}")
                    continue

        if resultados:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
                writer.writeheader()
                writer.writerows(resultados)
            print(f"\n💾 CSV guardado como: {output_file}")
        else:
            print("⚠️ No se encontraron resultados en ningún tipo de causa")

        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="rol_idcausa.csv", help="Archivo de salida")
    parser.add_argument("--headful", action="store_true", help="Ejecutar en modo visible")
    args = parser.parse_args()

    run_scraper(output_file=args.out, headless=not args.headful)
