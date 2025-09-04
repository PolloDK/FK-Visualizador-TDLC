from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from datetime import date
from typing import Optional, List, Dict, Any
from app.services.calculos import (
    calcular_promedio_dias_fallo_general,
    calcular_promedio_dias_primer_tramite_general,
    calcular_promedio_dias_fallo,
    calcular_promedio_dias_primer_tramite,
    obtener_causas_esperando_fallo,
    dias_fallo_desde_audiencia, 
    dias_fallo_desde_inicio,
    promedio_trimestral_desde_audiencia, 
    promedio_trimestral_desde_inicio,
    contar_total_causas,
    calcular_estadisticas_reclamaciones,
    obtener_estadisticas_trimestrales
)

router = APIRouter()

@router.get("/promedio-dias-audiencia-general")
def promedio_dias_audiencia_general():
    return calcular_promedio_dias_fallo_general()

@router.get("/promedio-dias-inicio-general")
def promedio_dias_inicio_general():
    return calcular_promedio_dias_primer_tramite_general()

@router.get("/promedio-dias-fallo")
def promedio_dias_fallo(
    fecha_inicio: Optional[str] = Query(None, description="Formato dd-mm-aaaa"),
    fecha_fin: Optional[str] = Query(None, description="Formato dd-mm-aaaa"),
    tipo: str = Query("todos", description="contencioso | no contencioso | todos")
):
    return calcular_promedio_dias_fallo(fecha_inicio, fecha_fin, tipo)

@router.get("/promedio-dias-desde-primer-tramite")
def promedio_dias_desde_primer_tramite(
    fecha_inicio: Optional[str] = Query(None, description="Formato dd-mm-aaaa"),
    fecha_fin: Optional[str] = Query(None, description="Formato dd-mm-aaaa"),
    tipo: str = Query("todos", description="contencioso | no contencioso | todos")
):
    return calcular_promedio_dias_primer_tramite(fecha_inicio, fecha_fin, tipo)

@router.get("/causas-esperando-fallo")
def causas_esperando_fallo():
    return obtener_causas_esperando_fallo()

@router.get("/evolucion-diaria-audiencia")
def evolucion_dias_fallo_desde_audiencia(
    fecha_inicio: str = Query(None, description="Fecha inicio en formato dd-mm-yyyy"),
    fecha_fin: str = Query(None, description="Fecha fin en formato dd-mm-yyyy"),
    tipo: str = Query("todos", description="Tipo de procedimiento (contencioso, no contencioso, etc.)"),
):
    return dias_fallo_desde_audiencia(fecha_inicio, fecha_fin, tipo)

@router.get("/evolucion-diaria-inicio")
def evolucion_dias_fallo_desde_inicio(
    fecha_inicio: str = Query(None, description="Fecha inicio en formato dd-mm-yyyy"),
    fecha_fin: str = Query(None, description="Fecha fin en formato dd-mm-yyyy"),
    tipo: str = Query("todos", description="Tipo de procedimiento (contencioso, no contencioso, etc.)"),
):
    return dias_fallo_desde_inicio(fecha_inicio, fecha_fin, tipo)

@router.get("/promedio-trimestral-audiencia", response_model=List[Dict])
def get_promedio_trimestral_audiencia(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    tipo: str = Query("todos")
):
    """
    Calcula el promedio trimestral de días desde la audiencia hasta el fallo.
    """
    return promedio_trimestral_desde_audiencia(fecha_inicio, fecha_fin, tipo)


@router.get("/promedio-trimestral-inicio", response_model=List[Dict])
def get_promedio_trimestral_inicio(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    tipo: str = Query("todos")
):
    """
    Calcula el promedio trimestral de días desde el inicio del expediente hasta el fallo.
    """
    return promedio_trimestral_desde_inicio(fecha_inicio, fecha_fin, tipo)

@router.get("/total-causas")
def total_causas():
    return contar_total_causas()

@router.get("/reclamaciones/porcentaje-revocadas")
def estadisticas_reclamaciones(
    fecha_inicio: str = Query(..., example="01-01-2020"),
    fecha_fin: str = Query(..., example="31-12-2024"),
    tipo: str = Query("todos", example="contencioso")
):
    try:
        fecha_inicio_dt = pd.to_datetime(fecha_inicio, dayfirst=True)
        fecha_fin_dt = pd.to_datetime(fecha_fin, dayfirst=True)

        resultado = calcular_estadisticas_reclamaciones(
            fecha_inicio_dt,
            fecha_fin_dt,
            tipo
        )

        return {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "tipo": tipo,
            **resultado
        }
    except Exception as e:
        return {"error": str(e)}

@router.get(
    "/reclamaciones/revocaciones-trimestrales",
    response_model=List[Dict[str, Any]],
    summary="Obtener estadísticas trimestrales de reclamaciones y revocaciones"
)
def get_reclamaciones_revocaciones_trimestrales(
    fecha_inicio: str = Query(..., example="01-01-2020"),
    fecha_fin: str = Query(..., example="31-12-2024"),
    tipo: str = Query("todos", example="contencioso")
):
    """
    Devuelve estadísticas trimestrales sobre:
    - Total de causas,
    - Reclamaciones detectadas,
    - Revocaciones totales y parciales,
    en un período de tiempo determinado, agrupado por trimestre.
    """
    try:
        # Convertir fechas desde formato dd-mm-yyyy
        fecha_inicio_dt = pd.to_datetime(fecha_inicio, format="%d-%m-%Y", errors="raise")
        fecha_fin_dt = pd.to_datetime(fecha_fin, format="%d-%m-%Y", errors="raise")

        resultados = obtener_estadisticas_trimestrales(
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            tipo=tipo
        )

        return resultados

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar la solicitud: {str(e)}")