from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.database import get_db
from app.services import elegibilidad, formularios, pdf_generator

router = APIRouter(prefix="/documentos", tags=["Documentos"])


@router.get("/formulario/plantilla")
def plantilla_formulario():
    """Devuelve la estructura del formulario genérico de solicitud a rellenar."""
    return formularios.obtener_plantilla_formulario()


class InformeIn(BaseModel):
    empresa_id: int
    convocatoria_id: int


@router.post("/informe-elegibilidad")
def generar_informe(payload: InformeIn):
    """Genera y devuelve el PDF de informe de elegibilidad para descargar."""
    with get_db() as conn:
        empresa = conn.execute("SELECT * FROM empresas WHERE id=?", (payload.empresa_id,)).fetchone()
        conv = conn.execute("SELECT * FROM convocatorias_cache WHERE id=?", (payload.convocatoria_id,)).fetchone()
        if not empresa or not conv:
            raise HTTPException(404, "Empresa o convocatoria no encontrada")

        empresa_d, conv_d = dict(empresa), dict(conv)
        resultado = elegibilidad.analizar(empresa_d, conv_d)
        ruta = pdf_generator.generar_informe_elegibilidad(empresa_d, conv_d, resultado)

        conn.execute(
            """INSERT INTO documentos_generados (empresa_id, convocatoria_id, tipo, ruta_archivo)
               VALUES (?,?,?,?)""",
            (payload.empresa_id, payload.convocatoria_id, "informe_elegibilidad", ruta),
        )

    return FileResponse(ruta, media_type="application/pdf", filename=ruta.split("/")[-1])


class MemoriaIn(BaseModel):
    empresa_id: int
    convocatoria_id: int
    respuestas: dict[str, str]  # respuestas al formulario genérico


@router.post("/memoria-solicitud")
def generar_memoria(payload: MemoriaIn):
    """Valida el formulario rellenado y genera el PDF de memoria de solicitud."""
    errores = formularios.validar_respuestas(payload.respuestas)
    if errores:
        raise HTTPException(422, {"errores": errores})

    with get_db() as conn:
        empresa = conn.execute("SELECT * FROM empresas WHERE id=?", (payload.empresa_id,)).fetchone()
        conv = conn.execute("SELECT * FROM convocatorias_cache WHERE id=?", (payload.convocatoria_id,)).fetchone()
        if not empresa or not conv:
            raise HTTPException(404, "Empresa o convocatoria no encontrada")

        secciones = formularios.construir_respuestas_para_memoria(payload.respuestas)
        ruta = pdf_generator.generar_memoria_solicitud(dict(empresa), dict(conv), secciones)

        conn.execute(
            """INSERT INTO documentos_generados (empresa_id, convocatoria_id, tipo, ruta_archivo)
               VALUES (?,?,?,?)""",
            (payload.empresa_id, payload.convocatoria_id, "memoria_solicitud", ruta),
        )

    return FileResponse(ruta, media_type="application/pdf", filename=ruta.split("/")[-1])


@router.get("/historico/{empresa_id}")
def historico_documentos(empresa_id: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM documentos_generados WHERE empresa_id=? ORDER BY creado_en DESC",
            (empresa_id,),
        ).fetchall()
        return [dict(r) for r in rows]
