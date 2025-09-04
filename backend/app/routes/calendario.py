# backend/api/endpoints/calendario.py

from fastapi import APIRouter, Query
from typing import List, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORIC_DIR = DATA_DIR / "historic_data"

AUDIENCIAS_FILE = DATA_DIR / "calendario_audiencias.csv"
DETALLE_FILE = HISTORIC_DIR / "rol_idcausa_detalle_actualizado.csv"
ROL_INFO_FILE = HISTORIC_DIR / "rol_idcausa.csv"

router = APIRouter()

def parse_fecha_ddmmaaaa(fecha_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(fecha_str.strip(), "%d-%m-%Y")
    except:
        return None

@router.get("/calendario")
async def get_calendario(
    fecha_desde: Optional[str] = Query(None, example="02-09-2025"),
    fecha_hasta: Optional[str] = Query(None, example="01-01-2026"),
    tipos: Optional[List[str]] = Query(None),
    solo_futuras: bool = Query(True),
    busqueda: Optional[str] = Query(None)
):
    try:
        # Cargar calendario de audiencias
        df = pd.read_csv(AUDIENCIAS_FILE, dtype=str).fillna("")
        df["fecha_audiencia_dt"] = pd.to_datetime(df["fecha"], format="%d-%m-%Y", errors="coerce")
        df = df[~df["fecha_audiencia_dt"].isna()]
        hoy = pd.Timestamp.now().normalize()

        if solo_futuras:
            df = df[df["fecha_audiencia_dt"] >= hoy]

        if fecha_desde:
            desde = parse_fecha_ddmmaaaa(fecha_desde)
            if desde:
                df = df[df["fecha_audiencia_dt"] >= desde]

        if fecha_hasta:
            hasta = parse_fecha_ddmmaaaa(fecha_hasta)
            if hasta:
                df = df[df["fecha_audiencia_dt"] <= hasta]

        if tipos and "__ALL__" not in tipos:
            df = df[df["tipo_audiencia"].isin(tipos)]

        if busqueda:
            b = busqueda.strip().lower()
            df = df[df["rol"].str.lower().str.contains(b) | df["caratula"].str.lower().str.contains(b)]

        df = df.sort_values("fecha_audiencia_dt")

        # Cargar datos de idCausa y link desde CSV histórico
        df_id = pd.read_csv(ROL_INFO_FILE, dtype=str).fillna("")
        df_id["rol"] = df_id["rol"].str.strip().str.upper()
        df["rol"] = df["rol"].str.strip().str.upper()

        df = df.merge(df_id[["rol", "idcausa", "link"]], on="rol", how="left")

        # Armar respuesta JSON
        data = [
            {
                "fecha_audiencia": row.get("fecha", "").strip(),
                "hora": row.get("hora", "").strip(),
                "rol": row.get("rol", "").strip(),
                "caratula": row.get("caratula", "").strip(),
                "tipo_audiencia": row.get("tipo_audiencia", "").strip(),
                "estado": row.get("estado", "").strip(),
                "idcausa": row.get("idcausa", "").strip(),
                "link": row.get("link", "").strip()
            }
            for row in df.to_dict(orient="records")
        ]

        return data

    except Exception as e:
        print(f"❌ Error en /calendario: {e}")
        return []
