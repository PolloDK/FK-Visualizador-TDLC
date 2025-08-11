# notification_module/email_notifier.py

import smtplib
import csv
from pathlib import Path
from email.message import EmailMessage
import os

EMAIL_REMITENTE = os.getenv("EMAIL_REMITENTE")
EMAIL_CLAVE_APP = os.getenv("EMAIL_CLAVE_APP")
RUTA_CSV = Path("backend/data/notifications/notifications_emails.csv")

def cargar_emails():
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

def enviar_aviso_nuevo_documento(tipo: str, titulo: str, url: str, fecha: str):
    destinatarios = cargar_emails()
    if not destinatarios:
        print("❌ No hay destinatarios configurados. Revisa el archivo CSV.")
        return

    msg = EmailMessage()
    msg["Subject"] = f"🧾 Nuevo {tipo.upper()} del TDLC publicado"
    msg["From"] = EMAIL_REMITENTE
    msg["To"] = ", ".join(destinatarios)

    msg.set_content(
        f"""Se ha detectado un nuevo {tipo} publicado en el sitio del TDLC:

📌 Título: {titulo}
📅 Fecha de publicación: {fecha}
🔗 Enlace: {url}

Este mensaje fue generado automáticamente por el sistema FK.
"""
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_REMITENTE, EMAIL_CLAVE_APP)
            smtp.send_message(msg)
        print(f"📧 Correo enviado a {len(destinatarios)} destinatarios.")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
