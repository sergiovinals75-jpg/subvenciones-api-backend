"""
Motor de análisis de elegibilidad.
Compara el perfil de una empresa contra los requisitos (extraídos o inferidos)
de una convocatoria, y devuelve una puntuación + motivos.

Es un sistema de reglas transparente y auditable (no una caja negra de IA),
pensado para que el usuario entienda siempre POR QUÉ una subvención encaja
o no. Fácil de ampliar añadiendo nuevas reglas.
"""
from dataclasses import dataclass, field


@dataclass
class ResultadoElegibilidad:
    cumple: bool
    puntuacion: float  # 0-100
    motivos: list[str] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)


def analizar(empresa: dict, convocatoria: dict) -> ResultadoElegibilidad:
    motivos = []
    alertas = []
    puntos = 0
    puntos_max = 0

    # 1. Coincidencia geográfica (CCAA)
    puntos_max += 30
    ccaa_conv = (convocatoria.get("ccaa") or "").lower()
    ccaa_empresa = (empresa.get("ccaa") or "").lower()
    if not ccaa_conv or "nacional" in ccaa_conv or "estado" in ccaa_conv:
        puntos += 30
        motivos.append("Convocatoria de ámbito nacional: aplica a cualquier CCAA.")
    elif ccaa_empresa and ccaa_empresa in ccaa_conv:
        puntos += 30
        motivos.append(f"Coincide la comunidad autónoma ({empresa.get('ccaa')}).")
    else:
        alertas.append(
            f"La convocatoria parece dirigida a '{convocatoria.get('ccaa')}', "
            f"distinta de la ubicación de la empresa ({empresa.get('ccaa')})."
        )

    # 2. Tamaño de empresa / PYME
    puntos_max += 25
    texto_conv = f"{convocatoria.get('titulo','')} {convocatoria.get('descripcion','')}".lower()
    if "pyme" in texto_conv or "pequeña y mediana" in texto_conv:
        if empresa.get("es_pyme"):
            puntos += 25
            motivos.append("La empresa es PYME y la convocatoria está orientada a PYMEs.")
        else:
            alertas.append("La convocatoria parece restringida a PYMEs y la empresa no lo es.")
    elif "autónomo" in texto_conv or "autonomo" in texto_conv:
        if empresa.get("autonomo"):
            puntos += 25
            motivos.append("La empresa está registrada como autónomo, requisito de la convocatoria.")
        else:
            alertas.append("La convocatoria parece dirigida a autónomos.")
    else:
        puntos += 15  # sin restricción clara detectada, puntuación neutra-positiva
        motivos.append("No se detectan restricciones explícitas de tamaño de empresa.")

    # 3. Sector / CNAE
    puntos_max += 25
    sector_conv = (convocatoria.get("sector") or "").lower()
    sector_empresa = (empresa.get("sector") or "").lower()
    if sector_conv and sector_empresa:
        if sector_empresa in sector_conv or sector_conv in sector_empresa:
            puntos += 25
            motivos.append(f"El sector de la empresa ({empresa.get('sector')}) coincide con el de la convocatoria.")
        else:
            puntos += 5
            alertas.append(
                f"El sector declarado de la convocatoria ('{convocatoria.get('sector')}') "
                f"no coincide claramente con el de la empresa ('{empresa.get('sector')}'). Revisar bases."
            )
    else:
        puntos += 15
        motivos.append("No hay suficiente información de sector para descartar la convocatoria.")

    # 4. Plazo de solicitud abierto
    puntos_max += 20
    fecha_fin = convocatoria.get("fecha_fin_solicitud")
    if fecha_fin:
        from datetime import datetime
        try:
            fin = datetime.fromisoformat(fecha_fin[:10]).date()
            dias_restantes = (fin - datetime.now().date()).days
            if dias_restantes >= 0:
                puntos += 20
                motivos.append(f"Plazo de solicitud abierto ({dias_restantes} días restantes).")
                if dias_restantes <= 7:
                    alertas.append("¡Urgente! Quedan 7 días o menos para presentar la solicitud.")
            else:
                alertas.append("El plazo de solicitud ya ha finalizado.")
        except ValueError:
            puntos += 10
    else:
        puntos += 10
        motivos.append("No se especifica fecha límite; verificar directamente en las bases.")

    puntuacion = round((puntos / puntos_max) * 100, 1) if puntos_max else 0
    cumple = puntuacion >= 60 and not any("ya ha finalizado" in a for a in alertas)

    return ResultadoElegibilidad(
        cumple=cumple, puntuacion=puntuacion, motivos=motivos, alertas=alertas
    )
