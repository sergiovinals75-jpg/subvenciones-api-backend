from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/empresas", tags=["Empresas"])


class EmpresaIn(BaseModel):
    nombre: str
    cif: str | None = None
    ccaa: str
    provincia: str | None = None
    municipio: str | None = None
    cnae: str | None = None
    sector: str | None = None
    num_empleados: int | None = None
    facturacion_anual: float | None = None
    antiguedad_anos: int | None = None
    es_pyme: bool = True
    autonomo: bool = False


@router.post("")
def crear_empresa(empresa: EmpresaIn):
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO empresas
               (nombre, cif, ccaa, provincia, municipio, cnae, sector,
                num_empleados, facturacion_anual, antiguedad_anos, es_pyme, autonomo)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (empresa.nombre, empresa.cif, empresa.ccaa, empresa.provincia,
             empresa.municipio, empresa.cnae, empresa.sector, empresa.num_empleados,
             empresa.facturacion_anual, empresa.antiguedad_anos,
             int(empresa.es_pyme), int(empresa.autonomo)),
        )
        return {"id": cur.lastrowid, **empresa.model_dump()}


@router.get("")
def listar_empresas():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM empresas ORDER BY creado_en DESC").fetchall()
        return [dict(r) for r in rows]


@router.get("/{empresa_id}")
def obtener_empresa(empresa_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM empresas WHERE id=?", (empresa_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Empresa no encontrada")
        return dict(row)
