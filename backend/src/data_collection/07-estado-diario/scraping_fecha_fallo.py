# build_rol_idcausa_map.py
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import csv, os, re, time
from datetime import datetime
from dateutil.relativedelta import relativedelta

CSV_CALENDARIO = "backend/data/calendar/calendario_audiencias.csv"
CSV_MAPA = "backend/data/calendar/rol_idcausa.csv"
BASE = "https://consultas.tdlc.cl"
HEADLESS = False
WAIT = 20000  # ms

# ---------------- utils ----------------
def cargar_roles_desde_calendario(path):
    roles = []
    seen = set()
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe {path}")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rol = (r.get("rol") or "").strip()
            if rol and rol not in seen:
                seen.add(rol)
                roles.append(rol)
    return roles

def cargar_mapa_existente(path):
    mapa = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rol = (r.get("rol") or "").strip()
                idc = (r.get("idCausa") or "").strip()
                if rol and idc:
                    mapa[rol] = idc
    return mapa

def append_mapa(path, nuevos: list[dict]):
    if not nuevos:
        return 0
    first = not os.path.exists(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rol","idCausa"])
        if first:
            w.writeheader()
        w.writerows(nuevos)
    return len(nuevos)

# ---------------- scraping helpers ----------------
def _find_id_in_page_href(page, rol):
    """Busca un <a href='...estadoDiario?idCausa=XXXX'> en la fila que contenga el rol."""
    try:
        idc = page.evaluate(
            """(rol)=>{
              rol = (rol||"").toLowerCase();
              const links=[...document.querySelectorAll("a[href*='estadoDiario?idCausa=']")];
              for(const a of links){
                const tr=a.closest("tr");
                const txt=(tr? tr.innerText : document.body.innerText).toLowerCase();
                if(txt.includes(rol)){
                  try{
                    const u=new URL(a.getAttribute('href'), location.origin);
                    const v=u.searchParams.get('idCausa');
                    if(v) return v;
                  }catch(e){}
                }
              }
              return null;
            }""",
            rol
        )
        return idc
    except Exception:
        return None

def _current_url_idcausa(page):
    try:
        u = page.url
        m = re.search(r"[?&]idCausa=(\d+)", u)
        return m.group(1) if m else None
    except Exception:
        return None

def buscar_idcausa_por_rol(page, rol: str) -> str | None:
    """
    Estrategia en cascada:
    1) Intento directo: /expediente?rol=<ROL> y busco link o redirección que revele idCausa.
    2) Fallback: /estadoDiario y busco un link a estadoDiario?idCausa en alguna tabla que contenga el rol.
       (Ajusta selectores de búsqueda si tu instancia exige filtrar antes de ver resultados.)
    """
    # 1) intento directo por rol
    try:
        page.goto(f"{BASE}/expediente?rol={rol}", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=WAIT)
        # ¿la URL ya trae idCausa?
        idc = _current_url_idcausa(page)
        if idc:
            return idc
        # ¿hay algún link al estadoDiario con el rol en la misma fila?
        idc = _find_id_in_page_href(page, rol)
        if idc:
            return idc
    except Exception:
        pass

    # 2) fallback: estadoDiario (buscar anclas con idCausa)
    try:
        page.goto(f"{BASE}/estadoDiario", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=WAIT)

        # Si hay filtro por rol, intenta rellenarlo (ajusta si tu UI difiere)
        # Probamos varios selectores razonables:
        for sel in ["input[name*='rol' i]", "input[placeholder*='rol' i]", "#rol", "#rolCausa"]:
            if page.locator(sel).count() > 0:
                page.fill(sel, rol)
                # buscar/filtrar
                for bsel in ["button:has-text('Buscar')", "button:has-text('Filtrar')", "button[aria-label='Buscar']"]:
                    if page.locator(bsel).count() > 0:
                        page.click(bsel)
                        break
                # si no hay botón, Enter
                page.keyboard.press("Enter")
                break

        # Espera algo de tabla o texto
        try:
            page.wait_for_timeout(800)  # breve respiro de render
            page.wait_for_load_state("networkidle", timeout=WAIT)
        except Exception:
            pass

        idc = _find_id_in_page_href(page, rol)
        if idc:
            return idc
    except Exception:
        pass

    return None

# ---------------- main ----------------
def main():
    roles = cargar_roles_desde_calendario(CSV_CALENDARIO)
    mapa = cargar_mapa_existente(CSV_MAPA)

    pendientes = [r for r in roles if r not in mapa]
    print(f"Roles totales: {len(roles)} | ya mapeados: {len(mapa)} | por resolver: {len(pendientes)}")

    nuevos = []
    if not pendientes:
        print("No hay roles nuevos por resolver.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()
        page.set_default_timeout(WAIT)

        for i, rol in enumerate(pendientes, start=1):
            print(f"[{i}/{len(pendientes)}] Resolviendo idCausa para rol {rol} ...")
            try:
                idc = buscar_idcausa_por_rol(page, rol)
                if idc:
                    print(f"  ➜ {rol} → idCausa={idc}")
                    nuevos.append({"rol": rol, "idCausa": idc})
                    mapa[rol] = idc
                else:
                    print(f"  ⚠️ {rol}: no se encontró idCausa (revisar selectores/filtros)")
            except Exception as e:
                print(f"  ⚠️ {rol}: error {e}")
            # pausita para no saturar
            time.sleep(0.2)

        browser.close()

    if nuevos:
        n = append_mapa(CSV_MAPA, nuevos)
        print(f"\n✅ Agregadas {n} filas nuevas a {CSV_MAPA}")
    else:
        print("\n🟰 No se agregaron filas nuevas.")

if __name__ == "__main__":
    main()
