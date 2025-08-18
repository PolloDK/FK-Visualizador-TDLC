from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import csv, os, time, json
from datetime import datetime
from dateutil.relativedelta import relativedelta

class CalendarioHistoricScraper:
    def __init__(
        self,
        url="https://consultas.tdlc.cl/audiencia",
        output_path="backend/data/calendar/calendario_audiencias.csv",
        checkpoint_path="backend/data/calendar/calendario_audiencias.checkpoint",
        limite_meses_sin_datos=3,
        headless=True,
    ):
        self.url = url
        self.output_path = output_path
        self.checkpoint_path = checkpoint_path
        self.limite_meses_sin_datos = limite_meses_sin_datos
        self.meses_sin_resultados = 0
        self.keys_existentes = set()  # para deduplicar (fecha,hora,rol)
        self.header = ["fecha","hora","rol","caratula","tipo_audiencia","estado","doc_resolucion"]
        self.MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless

    # ============== Navegador ==============
    def iniciar_navegador(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        self.page.set_default_timeout(20_000)
        self.page.goto(self.url, wait_until="domcontentloaded")
        self.page.wait_for_selector("div.controls", timeout=20_000)
        print("🌐 Navegador iniciado y calendario visible")

    def cerrar_navegador(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🔒 Navegador cerrado correctamente")

    # ============== Esperas/UI ==============
    def _wait_calendar_settled(self, screenshot_name=None):
        self.page.wait_for_load_state("networkidle", timeout=15_000)
        self.page.wait_for_selector("table#selectable tbody", timeout=15_000)
        try:
            self.page.wait_for_function(
                """() => {
                    const tbody = document.querySelector('table#selectable tbody');
                    if (!tbody) return false;
                    const rows = tbody.querySelectorAll('tr');
                    const emptyMsg = document.body.innerText.toLowerCase().includes('no hay audiencias')
                                   || document.body.innerText.toLowerCase().includes('no existen resultados');
                    return rows.length > 0 || emptyMsg;
                }""",
                timeout=15_000
            )
        except PWTimeout:
            if screenshot_name:
                self.page.screenshot(path=screenshot_name)
            raise

    def _wait_title_change(self, old_month_text, old_year_text, timeout=15_000):
        self.page.wait_for_function(
            """
            (args) => {
                const m = document.querySelector('div.title-month span')?.textContent?.trim().toLowerCase();
                const y = document.querySelector('div.title-year span')?.textContent?.trim();
                return m && y && (m !== args.oldM || y !== args.oldY);
            }""",
            arg={"oldM": old_month_text, "oldY": old_year_text},
            timeout=timeout
        )
        self._wait_calendar_settled("after_title_change.png")

    def _mes_idx(self, nombre_mes):
        return self.MESES.index(nombre_mes.lower()) + 1

    def _read_month_year(self):
        m = self.page.locator("div.title-month span").first.text_content(timeout=5000).strip().lower()
        y = int(self.page.locator("div.title-year span").first.text_content(timeout=5000).strip())
        return m, y

    def click_prev_month(self):
        btn = self.page.locator("span.previus-month")  # (sic) 'previus'
        if btn.count() == 0:
            return False
        oldM, oldY = self._read_month_year()
        btn.first.scroll_into_view_if_needed()
        btn.first.click(force=True)
        self._wait_title_change(oldM, str(oldY))
        return True

    def click_next_month(self):
        btn = self.page.locator("span.next-month")
        if btn.count() == 0:
            return False
        oldM, oldY = self._read_month_year()
        btn.first.scroll_into_view_if_needed()
        btn.first.click(force=True)
        self._wait_title_change(oldM, str(oldY))
        return True

    def ir_a_mes(self, mes_deseado, anio_deseado):
        objetivo_mes_txt = self.MESES[mes_deseado-1]
        objetivo_anio = int(anio_deseado)

        print(f"\n🔄 Navegando al mes: {objetivo_mes_txt} {objetivo_anio}")
        self.page.wait_for_selector("div.controls", timeout=20_000)

        mes_actual_txt, anio_actual = self._read_month_year()
        m_cur = self._mes_idx(mes_actual_txt)
        m_dst = mes_deseado
        delta = (anio_actual - objetivo_anio) * 12 + (m_cur - m_dst)

        if abs(delta) > 120:
            raise Exception(f"Delta de meses excesivo ({delta}). Revisa títulos o selectores.")

        if delta > 0:
            for _ in range(delta):
                if not self.click_prev_month():
                    self.page.screenshot(path="error_prev_month.png")
                    raise Exception("No se pudo hacer click en 'previus-month'.")
        elif delta < 0:
            for _ in range(-delta):
                if not self.click_next_month():
                    self.page.screenshot(path="error_next_month.png")
                    raise Exception("No se pudo hacer click en 'next-month'.")

        mes_actual_txt, anio_actual = self._read_month_year()
        print(f"📍 Calendario está en: {mes_actual_txt} {anio_actual}")
        if not (mes_actual_txt == objetivo_mes_txt and anio_actual == objetivo_anio):
            raise Exception(f"No se alcanzó {objetivo_mes_txt} {objetivo_anio}. Estoy en {mes_actual_txt} {anio_actual}")

        print("✅ Mes y año correctos encontrados.")
        self._wait_calendar_settled("error_wait_settle_mes.png")

        # Mostrar mes completo si existe
        ver_mes = self.page.locator("button:has-text('Ver Mes Completo'), a:has-text('Ver Mes Completo')")
        if ver_mes.count() > 0:
            try:
                ver_mes.first.click()
                self._wait_calendar_settled("after_ver_mes_completo.png")
            except Exception:
                pass

    # ============== Extracción/Paginación ==============
    def extraer_audiencias_mes(self):
        rows = self.page.locator("table#selectable tbody tr")
        n = rows.count()
        data = []
        for i in range(n):
            row = rows.nth(i)
            cols = row.locator("td")
            if cols.count() < 7:
                continue
            try:
                fecha = cols.nth(0).inner_text().strip()
                hora = cols.nth(1).inner_text().strip()
                rol = cols.nth(2).inner_text().strip()
                caratula = cols.nth(3).inner_text().strip()
                tipo = cols.nth(4).inner_text().strip()
                estado = cols.nth(5).inner_text().strip()
                link_a = cols.nth(6).locator("a")
                doc_res = link_a.get_attribute("href") if link_a.count() > 0 else ""
                data.append({
                    "fecha": fecha, "hora": hora, "rol": rol, "caratula": caratula,
                    "tipo_audiencia": tipo, "estado": estado, "doc_resolucion": doc_res
                })
            except Exception:
                continue
        return data

    def _click_siguiente_if_possible(self):
        next_btn = self.page.locator(
            "ul.box-pagination-calendar li:not(.disabled) a[aria-label='Next'], "
            "ul.box-pagination-calendar li:not(.disabled) a:has-text('Siguiente')"
        )
        if next_btn.count() > 0:
            next_btn.first.click()
            self._wait_calendar_settled("error_next_wait.png")
            return True
        next_symbol = self.page.locator(
            "ul.box-pagination-calendar li:not(.disabled) a:has-text('»'), "
            "ul.box-pagination-calendar li:not(.disabled) a:has-text('>')"
        )
        if next_symbol.count() > 0:
            next_symbol.first.click()
            self._wait_calendar_settled("error_next_symbol_wait.png")
            return True
        return False

    def scrape_mes(self, mes: int, anio: int):
        print(f"\n📅 Iniciando extracción de audiencias para {mes:02d}-{anio}")
        self.ir_a_mes(mes, anio)

        audiencias_totales = []
        while True:
            try:
                self.page.wait_for_selector("table#selectable tbody", timeout=10_000)
            except PWTimeout:
                self.page.screenshot(path=f"error_audiencia_{mes:02d}-{anio}.png")
                print(f"⚠️ Tabla de audiencias no encontrada en {mes:02d}-{anio}.")
                break

            time.sleep(0.5)
            audiencias = self.extraer_audiencias_mes()
            if not audiencias and len(audiencias_totales) == 0:
                print(f"⚠️ Mes {mes:02d}-{anio} sin audiencias.")
                break

            audiencias_totales.extend(audiencias)

            if not self._click_siguiente_if_possible():
                break

        print(f"📦 {len(audiencias_totales)} filas en {mes:02d}-{anio}")
        return audiencias_totales

    # ============== Persistencia/Deduplicación ==============
    def _cargar_keys_existentes(self):
        if not os.path.exists(self.output_path):
            return
        with open(self.output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                key = (r.get("fecha",""), r.get("hora",""), r.get("rol",""))
                self.keys_existentes.add(key)

    def _append_mes_csv(self, filas_mes):
        """Guarda (append) un mes ya scrapeado con deduplicación. Crea encabezado si no existe."""
        if not filas_mes:
            return 0
        nuevos = []
        for r in filas_mes:
            key = (r.get("fecha",""), r.get("hora",""), r.get("rol",""))
            if key not in self.keys_existentes:
                nuevos.append(r)
                self.keys_existentes.add(key)

        if not nuevos:
            print("🟰 Nada nuevo para agregar (todo duplicado).")
            return 0

        first_write = not os.path.exists(self.output_path)
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.header)
            if first_write:
                writer.writeheader()
            writer.writerows(nuevos)
        print(f"💾 {len(nuevos)} filas (mes) agregadas a {self.output_path}")
        return len(nuevos)

    # ============== Reanudación ==============
    def _leer_checkpoint(self):
        if os.path.exists(self.checkpoint_path):
            try:
                with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                y = data.get("ultimo_anio")
                m = data.get("ultimo_mes")
                if y and m:
                    return int(y), int(m)
            except Exception:
                pass
        return None

    def _escribir_checkpoint(self, anio, mes):
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump({"ultimo_anio": anio, "ultimo_mes": mes}, f)

    def _leer_mes_inicio(self):
        """
        Si hay checkpoint -> partir desde el mes anterior al último guardado (continuar hacia atrás).
        Si no hay checkpoint:
          - si hay CSV, partir desde mes anterior al más antiguo en CSV;
          - si no hay CSV, partir desde mes anterior al actual (hacia atrás).
        """
        # 1) checkpoint
        cp = self._leer_checkpoint()
        if cp:
            y, m = cp
            inicio = datetime(y, m, 1) - relativedelta(months=1)
            return inicio.month, inicio.year

        # 2) CSV existente
        if os.path.exists(self.output_path):
            fechas = []
            with open(self.output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r.get("fecha"):
                        try:
                            fechas.append(datetime.strptime(r["fecha"], "%d-%m-%Y"))
                        except Exception:
                            continue
            if fechas:
                mas_antigua = min(fechas)
                inicio = (mas_antigua.replace(day=1) - relativedelta(months=1))
                return inicio.month, inicio.year

        # 3) por defecto: mes anterior al actual
        hoy = datetime.today()
        inicio = hoy.replace(day=1) - relativedelta(months=1)
        return inicio.month, inicio.year

    # ============== Loop principal ==============
    def correr_hacia_atras(self, fecha_corte=None, solo_vista_causa=False):
        """
        fecha_corte: datetime(YYYY, MM, 1) -> se detiene cuando va a pasar de esa fecha.
        solo_vista_causa: si True, filtra 'tipo_audiencia' == 'Vista de la causa' antes de guardar.
        """
        self.iniciar_navegador()
        self._cargar_keys_existentes()

        # Punto de partida
        mes_actual, anio_actual = self._leer_mes_inicio()
        print(f"🚦 Inicio desde: {mes_actual:02d}-{anio_actual} (según checkpoint/CSV)")

        meses_sin = 0
        while meses_sin < self.limite_meses_sin_datos:
            # fecha de corte
            if fecha_corte:
                limite = datetime(anio_actual, mes_actual, 1)
                if limite < fecha_corte:
                    print(f"⏹ Llegamos a la fecha de corte: {fecha_corte.strftime('%m-%Y')}")
                    break

            # Scrape del mes
            filas_mes = self.scrape_mes(mes_actual, anio_actual)

            # Filtro opcional
            if solo_vista_causa and filas_mes:
                filas_mes = [r for r in filas_mes if r.get("tipo_audiencia","").strip().lower() == "vista de la causa"]

            if filas_mes:
                # Guardar inmediatamente este mes
                self._append_mes_csv(filas_mes)
                # Actualizar checkpoint a ESTE mes (ya persistido)
                self._escribir_checkpoint(anio_actual, mes_actual)
                meses_sin = 0
            else:
                meses_sin += 1
                print(f"⚠️ Sin audiencias en {mes_actual:02d}-{anio_actual} ({meses_sin}/{self.limite_meses_sin_datos})")

            # Retroceder un mes
            dt = datetime(anio_actual, mes_actual, 1) - relativedelta(months=1)
            mes_actual, anio_actual = dt.month, dt.year

        self.cerrar_navegador()


# ============== Ejecutable ==============
if __name__ == "__main__":
    scraper = CalendarioHistoricScraper(
        output_path="backend/data/notifications/calendario_audiencias.csv",
        checkpoint_path="backend/data/notifications/calendario_audiencias.checkpoint",
        limite_meses_sin_datos=6,
        headless=True,  # pon False si quieres ver la UI
    )
    # corta en enero 2018 si quieres: fecha_corte=datetime(2018,1,1)
    scraper.correr_hacia_atras(
        fecha_corte=None,
        solo_vista_causa=False  # True si quieres sólo “Vista de la causa”
    )
