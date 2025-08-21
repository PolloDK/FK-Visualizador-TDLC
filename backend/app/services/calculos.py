import pandas as pd
from pathlib import Path
from datetime import datetime
import pandas as pd
from pandas.tseries.offsets import MonthEnd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORIC_DIR = DATA_DIR / "historic_data"

AUDIENCIAS_FILE = DATA_DIR / "calendario_audiencias.csv"
DETALLE_FILE = HISTORIC_DIR / "rol_idcausa_detalle_actualizado.csv"
ROL_INFO_FILE = HISTORIC_DIR / "rol_idcausa.csv"

def calcular_promedio_dias_fallo_general():
    """
    Calcula el promedio de días entre la última audiencia relevante y el fallo para
    todas las causas, sin filtros de fecha o tipo.
    """
    # Cargar CSVs
    df_audiencias = pd.read_csv(AUDIENCIAS_FILE)
    df_detalle = pd.read_csv(DETALLE_FILE)
    df_info = pd.read_csv(ROL_INFO_FILE)

    # Normalizar columnas
    df_audiencias.columns = df_audiencias.columns.str.strip()
    df_info.columns = df_info.columns.str.strip().str.lower()
    df_detalle.columns = df_detalle.columns.str.strip()

    # Uppercase a 'rol' para hacer merge
    df_audiencias["rol"] = df_audiencias["rol"].astype(str).str.strip().str.upper()
    df_info["rol"] = df_info["rol"].astype(str).str.strip().str.upper()
    df_detalle["rol"] = df_detalle["rol"].astype(str).str.strip().str.upper()

    # Parsear fechas (formato explícito)
    df_audiencias["fecha"] = pd.to_datetime(df_audiencias["fecha"], format="%d-%m-%Y", errors="coerce")
    df_detalle["fecha_fallo"] = pd.to_datetime(df_detalle["fecha_fallo"], format="%d-%m-%Y", errors="coerce")

    # Merge audiencias con info de causa para obtener idcausa
    df_aud = pd.merge(df_audiencias, df_info[["rol", "idcausa"]], on="rol", how="left")

    # Filtrar audiencias tipo "Vista" o "Pública"
    df_aud = df_aud[df_aud["tipo_audiencia"].str.lower().str.contains("vista|pública", na=False)]

    # Obtener última audiencia relevante por idcausa
    df_aud_agg = df_aud.groupby("idcausa", as_index=False)["fecha"].max()
    df_aud_agg.rename(columns={"fecha": "fecha_audiencia"}, inplace=True)

    # Merge con detalle de fallo
    df_detalle.rename(columns={"idCausa": "idcausa"}, inplace=True)
    df_merged = pd.merge(df_detalle, df_aud_agg, on="idcausa", how="inner")
    
    # Calcular días
    df_merged["dias"] = (df_merged["fecha_fallo"] - df_merged["fecha_audiencia"]).dt.days
    df_merged = df_merged[df_merged["dias"] >= 0]
    
    # Calcular promedio y número de causas
    if df_merged.empty:
        return {"promedio_dias": None, "n_causas": 0}

    return {
        "promedio_dias": round(df_merged["dias"].mean(), 2),
        "n_causas": len(df_merged)
    }

def calcular_promedio_dias_primer_tramite_general():
    """
    Calcula el promedio de días entre el primer trámite y el fallo para
    todas las causas, sin filtros de fecha o tipo.
    """
    # Cargar datos
    df = pd.read_csv(DETALLE_FILE)

    # Normalizar columnas
    df.columns = df.columns.str.strip()
    df.rename(columns={"idCausa": "idcausa"}, inplace=True)

    df["rol"] = df["rol"].astype(str).str.strip().str.upper()
    
    # Parsear fechas (formato explícito)
    df["fecha_primer_tramite"] = pd.to_datetime(df["fecha_primer_tramite"], format="%d-%m-%Y", errors="coerce")
    df["fecha_fallo"] = pd.to_datetime(df["fecha_fallo"], format="%d-%m-%Y", errors="coerce")

    # Filtrar causas con ambas fechas
    df = df.dropna(subset=["fecha_primer_tramite", "fecha_fallo"])

    # Calcular diferencia de días
    df["dias"] = (df["fecha_fallo"] - df["fecha_primer_tramite"]).dt.days
    df = df[df["dias"] >= 0]
    
    # Calcular promedio y número de causas
    if df.empty:
        return {"promedio_dias": None, "n_causas": 0}

    return {
        "promedio_dias": round(df["dias"].mean(), 2),
        "n_causas": len(df)
    }

def calcular_promedio_dias_fallo(fecha_inicio=None, fecha_fin=None, tipo="todos"):
    # Cargar CSVs
    df_audiencias = pd.read_csv(AUDIENCIAS_FILE)
    df_detalle = pd.read_csv(DETALLE_FILE)
    df_info = pd.read_csv(ROL_INFO_FILE)

    # Normalizar columnas y formatos
    df_audiencias.columns = df_audiencias.columns.str.strip()
    df_info.columns = df_info.columns.str.strip().str.lower()
    df_detalle.columns = df_detalle.columns.str.strip()

    # Uppercase a 'rol' para hacer merge
    df_audiencias["rol"] = df_audiencias["rol"].astype(str).str.strip().str.upper()
    df_info["rol"] = df_info["rol"].astype(str).str.strip().str.upper()
    df_detalle["rol"] = df_detalle["rol"].astype(str).str.strip().str.upper()

    # Parsear fechas
    df_audiencias["fecha"] = pd.to_datetime(df_audiencias["fecha"], format="%d-%m-%Y", errors="coerce")
    df_detalle["fecha_fallo"] = pd.to_datetime(df_detalle["fecha_fallo"], format="%d-%m-%Y", errors="coerce")

    # Merge audiencias con info de causa para obtener idcausa
    df_aud = pd.merge(df_audiencias, df_info[["rol", "idcausa"]], on="rol", how="left")

    # Filtrar audiencias tipo "Vista" o "Pública"
    df_aud = df_aud[df_aud["tipo_audiencia"].str.lower().str.contains("vista|pública", na=False)]

    # Obtener última audiencia relevante por idcausa
    df_aud_agg = df_aud.groupby("idcausa", as_index=False)["fecha"].max()
    df_aud_agg.rename(columns={"fecha": "fecha_audiencia"}, inplace=True)

    # Merge con detalle de fallo (cambiamos idcausa -> idCausa)
    df_detalle = df_detalle.rename(columns={"idCausa": "idcausa"})
    df_merged = pd.merge(df_detalle, df_aud_agg, on="idcausa", how="inner")

    # Aplicar filtros por fecha
    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%d-%m-%Y")
            df_merged = df_merged[df_merged["fecha_fallo"] >= fecha_inicio]
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%d-%m-%Y")
            df_merged = df_merged[df_merged["fecha_fallo"] <= fecha_fin]
    except ValueError:
        return []

    
    # Agregar tipo de procedimiento
    df_merged = pd.merge(df_merged, df_info[["idcausa", "procedimiento"]], on="idcausa", how="left")

    if tipo != "todos":
        df_merged = df_merged[df_merged["procedimiento"].str.lower() == tipo.lower()]

    # Calcular días
    df_merged["dias"] = (df_merged["fecha_fallo"] - df_merged["fecha_audiencia"]).dt.days
    df_merged = df_merged[df_merged["dias"] >= 0]

    if df_merged.empty:
        return {"promedio_dias": None, "n_causas": 0}

    return {
        "promedio_dias": round(df_merged["dias"].mean(), 2),
        "n_causas": len(df_merged)
    }

def calcular_promedio_dias_primer_tramite(fecha_inicio=None, fecha_fin=None, tipo="todos"):
    # Cargar datos
    df = pd.read_csv(DETALLE_FILE)
    df_info = pd.read_csv(ROL_INFO_FILE)

    # Normalizar columnas
    df.columns = df.columns.str.strip()
    df_info.columns = df_info.columns.str.strip().str.lower()

    df["rol"] = df["rol"].astype(str).str.strip().str.upper()
    df_info["rol"] = df_info["rol"].astype(str).str.strip().str.upper()

    # Parsear fechas
    df["fecha_primer_tramite"] = pd.to_datetime(df["fecha_primer_tramite"], format="%d-%m-%Y", errors="coerce")
    df["fecha_fallo"] = pd.to_datetime(df["fecha_fallo"], format="%d-%m-%Y", errors="coerce")

    # Merge con info para obtener tipo
    df = pd.merge(df, df_info[["rol", "procedimiento"]], on="rol", how="left")

    # Filtros por fechas
    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%d-%m-%Y")
            df = df[df["fecha_fallo"] >= fecha_inicio]
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%d-%m-%Y")
            df = df[df["fecha_fallo"] <= fecha_fin]
        if tipo != "todos":
            df = df[df["procedimiento"].str.lower() == tipo.lower()]
    except ValueError:
        return []

    # Filtrar causas con ambas fechas
    df = df.dropna(subset=["fecha_primer_tramite", "fecha_fallo"])

    # Calcular diferencia de días
    df["dias"] = (df["fecha_fallo"] - df["fecha_primer_tramite"]).dt.days
    df = df[df["dias"] >= 0]

    if df.empty:
        return {"promedio_dias": None, "n_causas": 0}

    return {
        "promedio_dias": round(df["dias"].mean(), 2),
        "n_causas": len(df)
    }

def obtener_causas_esperando_fallo():
    # Cargar archivos
    df_aud = pd.read_csv(AUDIENCIAS_FILE)
    df_detalle = pd.read_csv(DETALLE_FILE)
    df_info = pd.read_csv(ROL_INFO_FILE)

    # Parsear fechas
    df_aud["fecha"] = pd.to_datetime(df_aud["fecha"], format="%d-%m-%Y", errors="coerce")
    df_detalle["fecha_fallo"] = pd.to_datetime(df_detalle["fecha_fallo"], format="%d-%m-%Y", errors="coerce")
    df_info["fecha_ingreso"] = pd.to_datetime(df_info["fecha_ingreso"], format="%d-%m-%Y", errors="coerce")

    # Unir audiencias con info de causa (para obtener idCausa, procedimiento, carátula, fecha ingreso)
    df_aud = df_aud.merge(
        df_info[["rol", "idcausa", "procedimiento", "descripcion", "fecha_ingreso"]],
        on="rol", how="left"
    )

    # Filtrar solo audiencias tipo vista o pública, y que hayan sido realizadas
    df_aud = df_aud[
        df_aud["tipo_audiencia"].str.lower().str.contains("vista|pública", na=False) &
        (df_aud["estado"].str.lower() == "realizada")
    ]

    # Obtener última audiencia relevante por idCausa
    df_aud_ult = df_aud.sort_values("fecha").drop_duplicates("idcausa", keep="last")
    df_aud_ult = df_aud_ult[[
        "idcausa", "rol", "fecha", "descripcion", "fecha_ingreso", "procedimiento"
    ]]
    df_aud_ult.rename(columns={
        "fecha": "fecha_audiencia",
        "descripcion": "caratula"
    }, inplace=True)

    # Causas sin fallo
    causas_sin_fallo = df_detalle[df_detalle["fallo_detectado"] == False][["idCausa"]]
    df_sin_fallo = causas_sin_fallo.merge(df_aud_ult, left_on="idCausa", right_on="idcausa", how="inner")

    # Calcular días desde audiencia
    df_sin_fallo["dias_desde_audiencia"] = (datetime.today() - df_sin_fallo["fecha_audiencia"]).dt.days

    # Causas con fallo para promedio
    df_con_fallo = df_detalle[df_detalle["fallo_detectado"] == True][["idCausa", "fecha_fallo"]]
    df_con_fallo = df_con_fallo.merge(
        df_aud_ult[["idcausa", "fecha_audiencia", "procedimiento"]],
        left_on="idCausa", right_on="idcausa", how="left"
    )
    df_con_fallo["dias_a_fallo"] = (df_con_fallo["fecha_fallo"] - df_con_fallo["fecha_audiencia"]).dt.days
    promedio_por_proc = df_con_fallo.dropna(subset=["dias_a_fallo"]).groupby("procedimiento")["dias_a_fallo"].mean().round().to_dict()

    # Estimar días restantes
    df_sin_fallo["dias_estimados_restantes"] = df_sin_fallo.apply(
        lambda row: max(int(promedio_por_proc.get(row["procedimiento"], 0) - row["dias_desde_audiencia"]), 0),
        axis=1
    )

    # Construir link al expediente
    df_sin_fallo["link"] = df_sin_fallo["idCausa"].apply(lambda x: f"https://consultas.tdlc.cl/estadoDiario?idCausa={x}")

    # Seleccionar columnas de salida
    resultado = df_sin_fallo[[
        "rol", "idCausa", "caratula", "fecha_ingreso", "fecha_audiencia",
        "dias_desde_audiencia", "dias_estimados_restantes", "link"
    ]].sort_values("dias_estimados_restantes")

    return resultado.to_dict(orient="records")

def dias_fallo_desde_audiencia(fecha_inicio=None, fecha_fin=None, tipo="todos"):
    df_audiencias = pd.read_csv(AUDIENCIAS_FILE)
    df_detalle = pd.read_csv(DETALLE_FILE)
    df_info = pd.read_csv(ROL_INFO_FILE)

    df_audiencias.columns = df_audiencias.columns.str.strip()
    df_info.columns = df_info.columns.str.strip().str.lower()
    df_detalle.columns = df_detalle.columns.str.strip()

    df_audiencias["rol"] = df_audiencias["rol"].astype(str).str.strip().str.upper()
    df_info["rol"] = df_info["rol"].astype(str).str.strip().str.upper()
    df_detalle["rol"] = df_detalle["rol"].astype(str).str.strip().str.upper()

    df_audiencias["fecha"] = pd.to_datetime(df_audiencias["fecha"], format="%d-%m-%Y", errors="coerce")
    df_detalle["fecha_fallo"] = pd.to_datetime(df_detalle["fecha_fallo"], format="%d-%m-%Y", errors="coerce")
    df_detalle["fecha_primer_tramite"] = pd.to_datetime(df_detalle["fecha_primer_tramite"], format="%d-%m-%Y", errors="coerce")

    df_aud = pd.merge(df_audiencias, df_info[["rol", "idcausa"]], on="rol", how="left")
    df_aud = df_aud[df_aud["tipo_audiencia"].str.lower().str.contains("vista|pública", na=False)]

    df_aud_agg = df_aud.groupby("idcausa", as_index=False)["fecha"].max()
    df_aud_agg.rename(columns={"fecha": "fecha_audiencia"}, inplace=True)

    df_detalle = df_detalle.rename(columns={"idCausa": "idcausa"})
    df = pd.merge(df_detalle, df_aud_agg, on="idcausa", how="inner")
    df = pd.merge(df, df_info[["idcausa", "procedimiento"]], on="idcausa", how="left")

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%d-%m-%Y")
            df = df[df["fecha_fallo"] >= fecha_inicio]
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%d-%m-%Y")
            df = df[df["fecha_fallo"] <= fecha_fin]
        if tipo != "todos":
            df = df[df["procedimiento"].str.lower() == tipo.lower()]
    except ValueError:
        return []

    df["dias"] = (df["fecha_fallo"] - df["fecha_audiencia"]).dt.days
    df = df[df["dias"] >= 0]
    
    df = df.sort_values(by="fecha_fallo", ascending=True)

    return df[["rol", "idcausa", "fecha_fallo", "dias", "procedimiento", "fecha_primer_tramite"]].dropna().to_dict(orient="records")

def dias_fallo_desde_inicio(fecha_inicio=None, fecha_fin=None, tipo="todos"):
    df = pd.read_csv(DETALLE_FILE)
    df_info = pd.read_csv(ROL_INFO_FILE)

    df.columns = df.columns.str.strip()
    df_info.columns = df_info.columns.str.strip().str.lower()

    df["rol"] = df["rol"].astype(str).str.strip().str.upper()
    df_info["rol"] = df_info["rol"].astype(str).str.strip().str.upper()

    df["fecha_primer_tramite"] = pd.to_datetime(df["fecha_primer_tramite"], format="%d-%m-%Y", errors="coerce")
    df["fecha_fallo"] = pd.to_datetime(df["fecha_fallo"], format="%d-%m-%Y", errors="coerce")

    df = pd.merge(df, df_info[["rol", "procedimiento"]], on="rol", how="left")

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%d-%m-%Y")
            df = df[df["fecha_fallo"] >= fecha_inicio]
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%d-%m-%Y")
            df = df[df["fecha_fallo"] <= fecha_fin]
        if tipo != "todos":
            df = df[df["procedimiento"].str.lower() == tipo.lower()]
    except ValueError:
        return []

    df = df.dropna(subset=["fecha_primer_tramite", "fecha_fallo"])
    df["dias"] = (df["fecha_fallo"] - df["fecha_primer_tramite"]).dt.days
    df = df[df["dias"] >= 0]
    
    df = df.sort_values(by="fecha_fallo", ascending=True)

    return df[["rol", "fecha_fallo", "dias", "procedimiento"]].dropna().to_dict(orient="records")

def contar_total_causas():
    try:
        df = pd.read_csv(DETALLE_FILE)
        df.columns = df.columns.str.strip().str.lower()
        if 'rol' not in df.columns:
            return {"error": "Columna 'rol' no encontrada en el archivo."}
        total = df['rol'].nunique()
        return {"total_causas": total}
    except Exception as e:
        return {"error": str(e)}