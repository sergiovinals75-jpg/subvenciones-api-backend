import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.services import buscador, elegibilidad

router = APIRouter(prefix="/subvenciones", tags=["Subvenciones"])


class BusquedaIn(BaseModel):
    descripcion: str = ""
    ccaa: str | None = None
    fecha_desde: str | None = None
    solo_abiertas: bool = True
    max_resultados: int = 30


@router.post("/buscar")
def buscar(payload: BusquedaIn):
    """Busca subvenciones nuevas en la BDNS (fuente oficial del Gobierno de España)."""
    try:
        resultados = buscador.buscar_convocatorias(
            descripcion=payload.descripcion,
            ccaa=payload.ccaa,
            fecha_desde=payload.fecha_desde,
            solo_abiertas=payload.solo_abiertas,
            max_resultados=payload.max_resultados,
        )
        return {"total": len(resultados), "convocatorias": resultados}
    except Exception as e:
        raise HTTPException(502, f"Error consultando la BDNS: {e}")


@router.get("/cache")
def cache(limit: int = 100):
    """Devuelve convocatorias ya buscadas previamente (sin llamar de nuevo a la BDNS)."""
    return buscador.listar_convocatorias_cacheadas(limit)


class AnalisisIn(BaseModel):
    empresa_id: int
    convocatoria_id: int  # id interno (convocatorias_cache.id)


@router.post("/analizar")
def analizar(payload: AnalisisIn):
    """Analiza si una empresa cumple los requisitos de una convocatoria cacheada."""
    with get_db() as conn:
        empresa_row = conn.execute("SELECT * FROM empresas WHERE id=?", (payload.empresa_id,)).fetchone()
        conv_row = conn.execute("SELECT * FROM convocatorias_cache WHERE id=?", (payload.convocatoria_id,)).fetchone()

        if not empresa_row:
            raise HTTPException(404, "Empresa no encontrada")
        if not conv_row:
            raise HTTPException(404, "Convocatoria no encontrada (búscala primero con /subvenciones/buscar)")

        empresa = dict(empresa_row)
        convocatoria = dict(conv_row)

        resultado = elegibilidad.analizar(empresa, convocatoria)

        conn.execute(
            """INSERT INTO analisis (empresa_id, convocatoria_id, cumple, puntuacion, motivos)
               VALUES (?,?,?,?,?)""",
            (payload.empresa_id, payload.convocatoria_id, int(resultado.cumple),
             resultado.puntuacion, json.dumps(resultado.motivos + resultado.alertas, ensure_ascii=False)),
        )

        return {
            "empresa": empresa["nombre"],
            "convocatoria": convocatoria["titulo"],
            "cumple": resultado.cumple,
            "puntuacion": resultado.puntuacion,
            "motivos": resultado.motivos,
            "alertas": resultado.alertas,
        }


@router.get("/analisis/{empresa_id}")
def historico_analisis(empresa_id: int):
    """Histórico de análisis realizados para una empresa, ordenado por puntuación."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT a.*, c.titulo, c.organo, c.fecha_fin_solicitud, c.importe_total
               FROM analisis a JOIN convocatorias_cache c ON a.convocatoria_id = c.id
               WHERE a.empresa_id=? ORDER BY a.puntuacion DESC""",
            (empresa_id,),
        ).fetchall()
        return [dict(r) for r in rows]
