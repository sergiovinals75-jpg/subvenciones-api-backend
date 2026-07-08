"""
Servicio de búsqueda de subvenciones.
Conecta con la API pública y gratuita de la BDNS (Base de Datos Nacional de
Subvenciones, Ministerio de Hacienda) a través de la librería bdns-fetch.

No requiere API key. Fuente oficial: https://www.infosubvenciones.es
"""
import json
import logging
from datetime import datetime
from typing import Optional

from bdns.fetch.client import BDNSClient

from app.database import get_db

logger = logging.getLogger(__name__)

_client: Optional[BDNSClient] = None


def _get_client() -> BDNSClient:
    global _client
    if _client is None:
        _client = BDNSClient()
    return _client


def buscar_convocatorias(
    descripcion: str = "",
    ccaa: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    solo_abiertas: bool = True,
    max_resultados: int = 50,
) -> list[dict]:
    """
    Busca convocatorias de subvenciones en la BDNS y las guarda en caché local.

    Args:
        descripcion: palabra clave a buscar (ej. "digitalización", "I+D", "empleo")
        ccaa: comunidad autónoma a filtrar (ej. "Comunitat Valenciana")
        fecha_desde: fecha mínima de publicación "YYYY-MM-DD"
        solo_abiertas: si True, descarta convocatorias con plazo ya cerrado
        max_resultados: número máximo de convocatorias a devolver
    """
    client = _get_client()
    page_size = min(max_resultados, 1000)
    num_pages = max(1, (max_resultados // page_size) + 1)

    kwargs = {"pageSize": page_size, "num_pages": num_pages, "from_page": 0}
    if descripcion:
        kwargs["descripcion"] = descripcion
    if fecha_desde:
        kwargs["fechaDesde"] = fecha_desde

    resultados_crudos = list(client.fetch_convocatorias_busqueda(**kwargs))

    convocatorias = []
    hoy = datetime.now().date()

    for item in resultados_crudos:
        fecha_fin = item.get("fechaFinSolicitud") or item.get("fechaFin")
        if solo_abiertas and fecha_fin:
            try:
                fecha_fin_dt = datetime.fromisoformat(fecha_fin[:10]).date()
                if fecha_fin_dt < hoy:
                    continue
            except (ValueError, TypeError):
                pass

        conv_ccaa = item.get("descripcionCCAA") or item.get("ccaa") or ""
        if ccaa and ccaa.lower() not in conv_ccaa.lower():
            continue

        convocatoria = {
            "bdns_id": str(item.get("numeroConvocatoria") or item.get("id") or ""),
            "titulo": item.get("titulo") or item.get("descripcion") or "Sin título",
            "organo": item.get("nivel1") or item.get("organo") or "",
            "ccaa": conv_ccaa,
            "fecha_publicacion": item.get("fechaPublicacion") or "",
            "fecha_fin_solicitud": fecha_fin or "",
            "importe_total": item.get("importeTotal") or 0,
            "sector": item.get("sector") or item.get("tipoBeneficiario") or "",
            "descripcion": item.get("descripcion") or "",
            "url_bases": item.get("urlBasesReguladoras") or "",
            "raw_json": json.dumps(item, ensure_ascii=False),
        }
        convocatorias.append(convocatoria)
        _guardar_en_cache(convocatoria)

        if len(convocatorias) >= max_resultados:
            break

    return convocatorias


def _guardar_en_cache(conv: dict):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO convocatorias_cache
                (bdns_id, titulo, organo, ccaa, fecha_publicacion,
                 fecha_fin_solicitud, importe_total, sector, descripcion,
                 url_bases, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(bdns_id) DO UPDATE SET
                titulo=excluded.titulo,
                fecha_fin_solicitud=excluded.fecha_fin_solicitud,
                importe_total=excluded.importe_total,
                actualizado_en=CURRENT_TIMESTAMP
            """,
            (
                conv["bdns_id"], conv["titulo"], conv["organo"], conv["ccaa"],
                conv["fecha_publicacion"], conv["fecha_fin_solicitud"],
                conv["importe_total"], conv["sector"], conv["descripcion"],
                conv["url_bases"], conv["raw_json"],
            ),
        )


def listar_convocatorias_cacheadas(limit: int = 100) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM convocatorias_cache ORDER BY fecha_publicacion DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
