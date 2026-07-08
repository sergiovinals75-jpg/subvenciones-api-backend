"""
Generador de formularios dinámicos de solicitud.

Dado que cada convocatoria tiene su propio modelo oficial (normalmente un PDF
o Word específico del organismo), este módulo no intenta clonar cada formulario
oficial byte a byte. En su lugar:

  1. Genera un formulario estructurado GENÉRICO y completo (los campos que casi
     toda convocatoria española pide: datos identificativos, memoria técnica,
     presupuesto, declaraciones responsables...).
  2. El usuario rellena ese formulario una vez por empresa/proyecto.
  3. El sistema usa esas respuestas para producir la memoria de solicitud (PDF)
     y puede mapearlas a los campos exactos de un formulario oficial si se
     sube la plantilla (ver rellenar_plantilla_docx).

Esto es lo realista y mantenible: automatiza el 90% del trabajo repetitivo
y dexa el 10% específico de cada organismo para revisión humana rápida.
"""
from typing import Any

CAMPOS_FORMULARIO_GENERICO = [
    {"id": "datos_solicitante", "etiqueta": "Datos del solicitante", "tipo": "texto_largo",
     "ayuda": "Nombre/razón social, CIF, domicilio social, representante legal."},
    {"id": "descripcion_proyecto", "etiqueta": "Descripción del proyecto o actividad", "tipo": "texto_largo",
     "ayuda": "Qué se va a hacer, objetivos, y por qué encaja con el objeto de la convocatoria."},
    {"id": "presupuesto", "etiqueta": "Presupuesto detallado", "tipo": "tabla",
     "ayuda": "Desglose de partidas: personal, equipos, servicios externos, etc."},
    {"id": "cronograma", "etiqueta": "Cronograma de ejecución", "tipo": "texto_largo",
     "ayuda": "Fases y fechas estimadas de inicio y fin."},
    {"id": "impacto_esperado", "etiqueta": "Impacto / resultados esperados", "tipo": "texto_largo",
     "ayuda": "Empleo generado, facturación esperada, innovación, sostenibilidad, etc."},
    {"id": "declaracion_responsable", "etiqueta": "Declaración responsable", "tipo": "casillas",
     "ayuda": "Estar al corriente de pagos con Hacienda y Seguridad Social, no estar inhabilitado, no recibir doble financiación."},
]


def obtener_plantilla_formulario() -> list[dict]:
    return CAMPOS_FORMULARIO_GENERICO


def validar_respuestas(respuestas: dict[str, Any]) -> list[str]:
    """Devuelve una lista de errores/campos faltantes."""
    errores = []
    for campo in CAMPOS_FORMULARIO_GENERICO:
        valor = respuestas.get(campo["id"])
        if not valor:
            errores.append(f"Falta rellenar: {campo['etiqueta']}")
    return errores


def construir_respuestas_para_memoria(respuestas: dict[str, Any]) -> dict[str, str]:
    """Transforma las respuestas del formulario en secciones legibles para el PDF."""
    mapa_titulos = {c["id"]: c["etiqueta"] for c in CAMPOS_FORMULARIO_GENERICO}
    return {mapa_titulos.get(k, k): v for k, v in respuestas.items()}
