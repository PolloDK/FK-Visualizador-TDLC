import csv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from tqdm import tqdm

def normalizar_fecha(fecha_raw):
    if not fecha_raw:
        return ""
    
    meses = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "setiembre": "09", "octubre": "10",
        "noviembre": "11", "diciembre": "12"
    }

    try:
        partes = fecha_raw.strip().replace(",", "").split()
        mes = meses[partes[0].lower()]
        dia = partes[1].zfill(2)
        anio = partes[2]
        return f"{anio}-{mes}-{dia}"
    except Exception as e:
        print(f"❌ Error al formatear fecha '{fecha_raw}': {e}")
        return fecha_raw

def extraer_campos_detalle_resolucion(html):
    soup = BeautifulSoup(html, "html.parser")

    def extraer_por_titulo(titulo):
        seccion = soup.find("h2", string=lambda x: x and x.strip().lower() == titulo.lower())
        if not seccion:
            return ""
        columna_derecha = seccion.find_parent("div", class_="elementor-column").find_next_sibling("div")
        if not columna_derecha:
            return ""
        contenido = columna_derecha.select_one(".jet-listing-dynamic-field__content, .jet-listing-dynamic-terms__link")
        return contenido.get_text(separator=" ", strip=True) if contenido else ""

    fecha_raw = extraer_por_titulo("FECHA DE DICTACIÓN:")
    fecha = normalizar_fecha(fecha_raw)
    rol = extraer_por_titulo("ROL DE CAUSA:")
    procedimiento = extraer_por_titulo("PROCEDIMIENTO:")
    partes = extraer_por_titulo("PARTES:")
    ministros = extraer_por_titulo("MINISTROS Y MINISTRAS QUE CONCURREN AL ACUERDO:")
    redactor = extraer_por_titulo("REDACCIÓN:")
    conducta = extraer_por_titulo("CONDUCTA:")
    industria = extraer_por_titulo("INDUSTRIA:")
    articulo = extraer_por_titulo("ARTÍCULO (NORMA):")
    objeto_proceso = extraer_por_titulo("OBJETO DE PROCESO:")
    resultado = extraer_por_titulo("RESULTADO DEL TDLC:")
    voto_contra = extraer_por_titulo("VOTO EN CONTRA:")
    voto_prevencion = extraer_por_titulo("VOTO PREVENCIÓN:")
    
    # Resultado Excma. Corte Suprema
    resultado_cs = ""
    link_cs = ""

    # Buscar por contenido alternativo: "No se interpusieron recursos" o texto que esté dentro del widget
    posibles_bloques_cs = soup.find_all("div", class_="jet-listing-dynamic-field__content")
    for bloque in posibles_bloques_cs:
        texto = bloque.get_text(strip=True)
        if "No se interpusieron recursos" in texto or "Resultado Excma. Corte Suprema" in texto:
            resultado_cs = texto
            enlace = bloque.find("a")
            if enlace and enlace.has_attr("href"):
                link_cs = enlace["href"]
            break


    temas = extraer_por_titulo("TEMAS QUE TRATA:")

    titulo = soup.find("meta", property="og:title")
    caratula = titulo["content"].strip() if titulo else soup.title.string.strip()

    return {
        "fecha_dictacion": fecha,
        "caratula": caratula,
        "rol_causa": rol,
        "procedimiento": procedimiento,
        "partes": partes,
        "ministros_concuerdan": ministros,
        "ministro_redactor": redactor,
        "conducta": conducta,
        "industria": industria,
        "articulo_norma": articulo,
        "objeto_proceso": objeto_proceso,
        "resultado_tdlc": resultado,
        "voto_en_contra": voto_contra,
        "voto_prevencion": voto_prevencion,
        "resolucion_corte_suprema": resultado_cs,
        "link_resolucion_corte_suprema": link_cs,
        "temas_tratados": temas,
    }

def procesar_una_url(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Cargando {url}")
        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector(".elementor-section", timeout=15000)
            time.sleep(1)
            html = page.content()
            data = extraer_campos_detalle_resolucion(html)
            data["url"] = url
        except Exception as e:
            print(f"❌ Error con URL {url}: {e}")
            data = {
                "fecha_dictacion": "",
                "caratula": "",
                "rol_causa": "",
                "procedimiento": "",
                "partes": "",
                "ministros_concuerdan": "",
                "ministro_redactor": "",
                "conducta": "",
                "industria": "",
                "articulo_norma": "",
                "objeto_proceso": "",
                "resultado_tdlc": "",
                "voto_en_contra": "",
                "voto_prevencion": "",
                "resolucion_corte_suprema": "",
                "link_resolucion_corte_suprema": "",
                "temas_tratados": "",
                "url": url
            }
        browser.close()
        return data

# Leer el CSV con las URLs
with open("backend/data/resoluciones_listado.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    urls = [row["url_ficha"] for row in reader]

data_detalle = []
for url in tqdm(urls, desc="Procesando resoluciones"):
    resultado = procesar_una_url(url)
    data_detalle.append(resultado)
#data_detalle = [procesar_una_url(urls[0])]

# Guardar en CSV
output_file = "backend/data/resoluciones_detalle.csv"
with open(output_file, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "fecha_dictacion",
        "caratula",
        "rol_causa",
        "procedimiento",
        "partes",
        "ministros_concuerdan",
        "ministro_redactor",
        "conducta",
        "industria",
        "articulo_norma",
        "objeto_proceso",
        "resultado_tdlc",
        "voto_en_contra",
        "voto_prevencion",
        "resolucion_corte_suprema",
        "link_resolucion_corte_suprema",
        "temas_tratados",
        "url"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data_detalle)

print(f"✅ Datos extraídos y guardados en {output_file}")
