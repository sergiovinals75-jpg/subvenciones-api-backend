"""
Configuración de la base de datos SQLite para el Analista IA de Subvenciones.
Guarda perfiles de empresa, subvenciones encontradas y resultados de análisis.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "subvenciones.db"
DB_PATH.parent.mkdir(exist_ok=True)


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cif TEXT,
                ccaa TEXT NOT NULL,
                provincia TEXT,
                municipio TEXT,
                cnae TEXT,
                sector TEXT,
                num_empleados INTEGER,
                facturacion_anual REAL,
                antiguedad_anos INTEGER,
                es_pyme INTEGER DEFAULT 1,
                autonomo INTEGER DEFAULT 0,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS convocatorias_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bdns_id TEXT UNIQUE,
                titulo TEXT,
                organo TEXT,
                ccaa TEXT,
                fecha_publicacion TEXT,
                fecha_fin_solicitud TEXT,
                importe_total REAL,
                sector TEXT,
                descripcion TEXT,
                url_bases TEXT,
                raw_json TEXT,
                actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS analisis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL,
                convocatoria_id INTEGER NOT NULL,
                cumple INTEGER NOT NULL,
                puntuacion REAL,
                motivos TEXT,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id),
                FOREIGN KEY (convocatoria_id) REFERENCES convocatorias_cache(id)
            );

            CREATE TABLE IF NOT EXISTS documentos_generados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL,
                convocatoria_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                ruta_archivo TEXT NOT NULL,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id),
                FOREIGN KEY (convocatoria_id) REFERENCES convocatorias_cache(id)
            );
            """
        )


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
