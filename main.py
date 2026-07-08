from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import documentos, empresas, subvenciones

app = FastAPI(
    title="Analista IA de Subvenciones",
    description=(
        "API que busca subvenciones públicas españolas (fuente oficial BDNS), "
        "analiza si una empresa cumple los requisitos, prepara la documentación, "
        "rellena formularios y genera PDFs listos para presentar."
    ),
    version="1.0.0",
)

# Permite que la landing (u otro frontend) llame a esta API desde el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción, sustituir por el dominio exacto de la landing
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(empresas.router)
app.include_router(subvenciones.router)
app.include_router(documentos.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def raiz():
    return {
        "servicio": "Analista IA de Subvenciones",
        "estado": "operativo",
        "documentacion": "/docs",
    }


@app.get("/salud")
def salud():
    return {"estado": "ok"}
