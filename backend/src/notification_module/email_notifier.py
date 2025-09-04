import os
import csv
import smtplib
from email.message import EmailMessage
from email.utils import formataddr 
from pathlib import Path
import sys
import ssl

# Asegurar path absoluto al módulo si no se ejecuta como paquete
MODULE_DIR = Path(__file__).resolve().parent
sys.path.append(str(MODULE_DIR))

# Importar template de forma segura
try:
    from html_template import construir_html_email, construir_html_resumen_diario, PLANTILLAS_HTML
except ImportError as e:
    print(f"❌ Error importando el template HTML: {e}. Asegúrate de que html_template.py existe y tiene 'construir_html_email' y 'PLANTILLAS_HTML'.")
    construir_html_email = None
    construir_html_resumen_diario = None
    PLANTILLAS_HTML = None

EMAIL_REMITENTE = os.getenv("EMAIL_REMITENTE")
EMAIL_CLAVE_APP = os.getenv("EMAIL_CLAVE_APP")
RUTA_CSV = Path("backend/data/notifications/notifications_emails.csv")

def cargar_emails():
    """Carga los correos de los destinatarios desde un archivo CSV."""
    emails = []
    if not RUTA_CSV.exists():
        print(f"⚠️ Archivo no encontrado: {RUTA_CSV}")
        return emails
    with open(RUTA_CSV, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email = row.get("email", "").strip()
            if email:
                emails.append(email)
    return emails

def enviar_notificacion_evento(evento: dict):
    """
    Envía un único correo para un evento específico usando el template correcto.
    Esta es una versión refactorizada de 'enviar_aviso_nuevo_documento'.
    """
    destinatarios = cargar_emails()
    if not destinatarios:
        print("❌ No hay destinatarios configurados. Revisa el archivo CSV.")
        return

    # Usamos el tipo del evento para obtener el asunto del template
    plantilla = PLANTILLAS_HTML.get(evento["tipo"])
    if not plantilla:
        print(f"❌ No se encontró plantilla para el tipo de evento: {evento['tipo']}")
        return
        
    asunto = f"TDLC - {plantilla['nombre']} en caso {evento.get('rol', 'Sin Rol')}"

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = formataddr(("📊 FK Economics Data", EMAIL_REMITENTE))
    msg["To"] = ", ".join(destinatarios)

    # Construimos el HTML con la función del template
    # Los datos se pasan de forma dinámica desde el diccionario 'evento'
    html = construir_html_email(
        tipo=evento["tipo"],
        titulo=evento.get("titulo", ""), 
        url=evento.get("url", ""),        
        fecha=evento.get("fecha", ""),
        rol=evento.get("rol", ""),
        id_causa=evento.get("id_causa", "")
    )

    msg.set_content("Este correo contiene contenido en HTML. Usa un visor compatible.")
    msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_REMITENTE, EMAIL_CLAVE_APP)
            smtp.send_message(msg)
        print(f"📧 Correo '{evento['tipo']}' enviado a {len(destinatarios)} destinatarios.")
    except Exception as e:
        print(f"❌ Error al enviar correo para el evento '{evento['tipo']}': {e}")
    
def enviar_resumen_diario(fecha: str, total_tramites: int, eventos_del_dia: list, listado_tramites: list):
    """
    Orquesta el envío de notificaciones individuales para cada evento importante.
    Esta función ya no envía un resumen, sino una notificación por cada evento.
    """
    if not PLANTILLAS_HTML:
        print("❌ No se puede enviar el email de resumen. Los templates HTML no se cargaron correctamente.")
        return

    if not eventos_del_dia:
        print("✅ No se detectaron eventos importantes para enviar notificaciones.")
        return
        
    print(f"📧 Preparando {len(eventos_del_dia)} notificaciones para enviar...")
    for evento in eventos_del_dia:
        enviar_notificacion_evento(evento)
        
    print("✅ Proceso de envío de notificaciones completado.")
    
def enviar_correo_resumen_diario(fecha: str, total_tramites: int, listado_tramites: list):
    if not listado_tramites:
        print("ℹ️ No hay trámites que incluir en el correo resumen diario.")
        return

    if not PLANTILLAS_HTML or not construir_html_resumen_diario:
        print("❌ No se puede construir correo de resumen diario. Faltan plantillas o funciones.")
        return

    destinatarios = cargar_emails()
    if not destinatarios:
        print("❌ No hay destinatarios para enviar el resumen diario.")
        return

    asunto = f"📋 Resumen Diario TDLC – {fecha}"

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = formataddr(("📊 FK Economics Data", EMAIL_REMITENTE))
    msg["To"] = ", ".join(destinatarios)

    html = construir_html_resumen_diario(fecha, total_tramites, listado_tramites)
    msg.set_content("Este correo contiene contenido en HTML. Usa un visor compatible.")
    msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_REMITENTE, EMAIL_CLAVE_APP)
            smtp.send_message(msg)
        print(f"📬 Correo resumen del día enviado a {len(destinatarios)} destinatarios.")
    except Exception as e:
        print(f"❌ Error al enviar el correo resumen del día: {e}")

# Ejemplo de uso (el __main__ ya no necesita construir todo el HTML)
if __name__ == "__main__":
    # Audiencia vista
    evento_vista = {
        "tipo": "vista de la causa",
        "rol": "C-789-2025",
        "fecha": "27-08-2025",
        "id_causa": "12345", 
        "titulo": "Vista de la causa en materia de libre competencia",  
        "url": "https://consultas.tdlc.cl/audiencia?idCausa=12345"
    }
    enviar_notificacion_evento(evento_vista)