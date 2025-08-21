# Colores FK Economics
fk_primary = "#2697E1"
fk_secondary = "#222222"
fk_text = "#7C7B7E"
fk_bg = "#F7F7F7"

PLANTILLAS_HTML = {
    "fallo": {
        "color": "#E13A26",
        "nombre": "Fallo o Sentencia del TDLC",
        "cuerpo": f"""
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                Se ha publicado un <strong>Fallo o Sentencia</strong> en el TDLC.
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>📅 Fecha de publicación:</strong><br> {{fecha}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>⚖️ Rol de causa:</strong><br> {{rol}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>🆔 ID de causa:</strong><br> {{id_causa}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 20px;">
                <strong>📄 Título del documento:</strong><br> {{titulo}}
            </p>
        """
    },
    "reclamacion": {
        "color": "#FFA726",
        "nombre": "Nueva Reclamación",
        "cuerpo": f"""
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                Se ha detectado una nueva <strong>Reclamación</strong> en el TDLC.
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>📅 Fecha de publicación:</strong><br> {{fecha}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>⚖️ Rol de causa:</strong><br> {{rol}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>🆔 ID de causa:</strong><br> {{id_causa}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 20px;">
                <strong>📄 Título del documento:</strong><br> {{titulo}}
            </p>
        """
    },
    "conciliacion": {
        "color": "#2697E1",
        "nombre": "Conciliación del TDLC",
        "cuerpo": f"""
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                Se ha publicado un acta de <strong>Conciliación</strong> en el TDLC.
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>📅 Fecha de publicación:</strong><br> {{fecha}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>⚖️ Rol de causa:</strong><br> {{rol}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>🆔 ID de causa:</strong><br> {{id_causa}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 20px;">
                <strong>📄 Título del documento:</strong><br> {{titulo}}
            </p>
        """
    },
    "nueva_causa": {
        "color": "#4CAF50",
        "nombre": "Nueva Causa",
        "cuerpo": f"""
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                Se ha publicado una <strong>Nueva Causa</strong> en el TDLC.
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>📅 Fecha del primer trámite:</strong><br> {{fecha}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>⚖️ Rol de causa:</strong><br> {{rol}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 12px;">
                <strong>🆔 ID de causa:</strong><br> {{id_causa}}
            </p>
            <p style="font-size: 15px; color: {fk_text}; margin: 0 0 20px;">
                <strong>📄 Título / descripción:</strong><br> {{titulo}}
            </p>
        """
    },
    "resumen_diario": {
    "color": "#222222",
    "nombre": "Resumen Diario de Trámites del TDLC",
    "cuerpo": """
        <p style="font-size: 15px; color: {fk_text}; margin: 0 0 18px;">
            Este es el resumen de los trámites publicados en el Estado Diario del TDLC con fecha <strong>{fecha}</strong>.
        </p>
        <p style="font-size: 15px; color: {fk_text}; margin: 0 0 10px;">
            <strong>🔍 Total de trámites encontrados:</strong> {total_tramites}
        </p>
        {tabla_tramites}
        <p style="font-size: 14px; color: {fk_text}; margin-top: 30px;">
            Este correo ha sido generado automáticamente por el sistema de monitoreo de FK Economics.
        </p>
    """
}

}

def construir_html_email(tipo: str, titulo: str, url: str, fecha: str, rol: str, id_causa: str) -> str:
    # Colores FK Economics
    fk_primary = "#2697E1"
    fk_secondary = "#222222"
    fk_text = "#7C7B7E"
    fk_bg = "#F7F7F7"

    # Obtener la plantilla y el color según el tipo de notificación
    plantilla = PLANTILLAS_HTML.get(tipo, {})
    tipo_color = plantilla.get("color", fk_primary)
    tipo_nombre = plantilla.get("nombre", "Notificación del TDLC")
    cuerpo_html = plantilla.get("cuerpo", "<p>No hay contenido disponible para este tipo de notificación.</p>")

    # Formatear el cuerpo del HTML con los datos
    cuerpo_formateado = cuerpo_html.format(
        fk_text=fk_text,
        titulo=titulo,
        fecha=fecha,
        rol=rol,
        id_causa=id_causa,
        url=url
    )

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{tipo_nombre}</title>
    </head>
    <body style="margin: 0; padding: 20px; font-family: 'Arial', sans-serif; background-color: {fk_bg};">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: auto; background-color: #FFFFFF; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden;">
            <tr>
                <td style="background-color: {tipo_color}; color: white; padding: 20px 30px; font-size: 22px; font-weight: bold;">
                    {tipo_nombre} – Rol {rol}
                </td>
            </tr>
            <tr>
                <td style="padding: 30px;">
                    {cuerpo_formateado}
                    <a href="{url}" target="_blank" style="display: inline-block; background-color: {fk_primary}; color: #FFFFFF; text-decoration: none; padding: 12px 20px; border-radius: 5px; font-weight: bold; font-size: 14px;">
                        Ver causa completa
                    </a>
                </td>
            </tr>
            <tr>
                <td style="background-color: #F0F0F0; padding: 18px; text-align: center; font-size: 12px; color: {fk_text};">
                    Sistema de Monitoreo del TDLC — <strong>FK Economics</strong><br>
                    Este mensaje fue generado automáticamente.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
def construir_html_resumen_diario(fecha: str, total_tramites: int, listado_tramites: list) -> str:
    plantilla = PLANTILLAS_HTML.get("resumen_diario", {})
    tipo_color = plantilla.get("color", "#222222")
    tipo_nombre = plantilla.get("nombre", "Resumen Diario del TDLC")
    cuerpo_html = plantilla.get("cuerpo", "")

    # Convertimos la tabla de trámites en HTML
    if listado_tramites:
        columnas = ["Fecha", "Rol", "Referencia", "Tipo", "Firmantes", "Fojas"]
        filas_html = ""
        for tramite in listado_tramites:
            fila = "<tr>" + "".join(
                f"<td style='padding: 6px 10px; border: 1px solid #ccc; font-size: 13px;'>{tramite.get(col, '')}</td>"
                for col in columnas
            ) + "</tr>"
            filas_html += fila

        tabla_html = f"""
        <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
            <thead>
                <tr>{"".join(f"<th style='padding: 8px; background-color: #f0f0f0; border: 1px solid #ccc; text-align: left;'>{col}</th>" for col in columnas)}</tr>
            </thead>
            <tbody>{filas_html}</tbody>
        </table>
        """
    else:
        tabla_html = "<p style='color: #999;'>No se registraron trámites hoy.</p>"

    cuerpo_formateado = cuerpo_html.format(
        fk_text="#7C7B7E",
        fecha=fecha,
        total_tramites=total_tramites,
        tabla_tramites=tabla_html
    )

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{tipo_nombre}</title>
    </head>
    <body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; background-color: #F7F7F7;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 700px; margin: auto; background-color: #FFFFFF; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden;">
            <tr>
                <td style="background-color: {tipo_color}; color: white; padding: 20px 30px; font-size: 20px; font-weight: bold;">
                    {tipo_nombre} – {fecha}
                </td>
            </tr>
            <tr>
                <td style="padding: 30px;">
                    {cuerpo_formateado}
                </td>
            </tr>
            <tr>
                <td style="background-color: #F0F0F0; padding: 18px; text-align: center; font-size: 12px; color: #7C7B7E;">
                    Sistema de Monitoreo del TDLC — <strong>FK Economics</strong><br>
                    Este mensaje fue generado automáticamente.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
