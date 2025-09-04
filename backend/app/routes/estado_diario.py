from fastapi import APIRouter, HTTPException
import pandas as pd
import os
from pathlib import Path

# Define la ruta base para los archivos temporales del estado diario
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

CAUSAS_DEL_DIA_FILE = DATA_DIR / "estado_diario" / "estado_diario_tmp.csv"
TRAMITES_DETALLE_FILE = DATA_DIR / "estado_diario" / "estado_diario_detalle_tmp.csv"

# Crea un enrutador de FastAPI.
# Esto permite que los endpoints sean modulares y se puedan incluir en la aplicación principal (por ejemplo, en main.py)
router = APIRouter()

@router.get("/causas-del-dia")
def get_causas_del_dia():
    """
    Endpoint para obtener la lista de causas publicadas en el estado diario del día.
    Devuelve la información completa de cada causa, incluyendo rol, descripción, trámites y link.
    """
    if not os.path.exists(CAUSAS_DEL_DIA_FILE):
        raise HTTPException(status_code=404, detail="Archivo de causas del día no encontrado.")
    
    try:
        df = pd.read_csv(CAUSAS_DEL_DIA_FILE, dtype=str)
        # Selecciona las columnas solicitadas y las convierte en una lista de diccionarios
        df_selected = df[["fecha_estado_diario", "rol", "descripcion", "tramites", "link"]]
        causas_del_dia = df_selected.to_dict(orient="records")
        return {"causas_del_dia": causas_del_dia}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el archivo: {e}")

@router.get("/tramites-del-dia")
def get_tramites_del_dia():
    if not os.path.exists(TRAMITES_DETALLE_FILE):
        raise HTTPException(status_code=404, detail="Archivo de trámites del día no encontrado.")
    
    try:
        df = pd.read_csv(TRAMITES_DETALLE_FILE, dtype=str, on_bad_lines='skip', engine='python').fillna('')
        
        columnas_esperadas = ["idCausa", "rol", "TipoTramite", "Fecha", "Referencia", "Foja", "Link_Descarga", "Tiene_Detalles", "Tiene_Firmantes"]
        
        if df.empty or not all(col in df.columns for col in columnas_esperadas):
            return []

        df = df[columnas_esperadas].replace({'nan': '', 'inf': '', '-inf': ''})

        return df.to_dict(orient="records")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el archivo: {e}")