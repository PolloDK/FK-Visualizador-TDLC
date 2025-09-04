from fastapi import FastAPI
from app.routes import causas, estado_diario, calendario
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="API Visualizador TDLC",
    description="Calcula métricas sobre causas del TDLC",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(causas.router, prefix="/causas", tags=["Causas"])
app.include_router(estado_diario.router, prefix="/estado-diario", tags=["Estado Diario"])
app.include_router(calendario.router, prefix="/calendario", tags=["Calendario"])
