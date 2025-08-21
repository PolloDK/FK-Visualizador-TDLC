from fastapi import APIRouter, Query
from typing import Optional
from app.services.calculos import (
    calcular_promedio_dias_fallo_general,
    calcular_promedio_dias_primer_tramite_general,
    calcular_promedio_dias_fallo,
    calcular_promedio_dias_primer_tramite,
    obtener_causas_esperando_fallo,
    dias_fallo_desde_audiencia, 
    dias_fallo_desde_inicio,
    contar_total_causas
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

@router.get("/total-causas")
def total_causas():
    return contar_total_causas()