"""
Generación de documentos PDF:
  1. Informe de elegibilidad (resultado del análisis para una convocatoria)
  2. Memoria/dossier de solicitud (documentación preparada para presentar)

Usa ReportLab, no requiere binarios externos ni licencias.
"""
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "generados"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TituloPrincipal", fontSize=18, spaceAfter=16, textColor=colors.HexColor("#1a3c6e")))
styles.add(ParagraphStyle(name="Subtitulo", fontSize=13, spaceAfter=10, textColor=colors.HexColor("#2c5aa0")))
styles.add(ParagraphStyle(name="Cuerpo", fontSize=10, spaceAfter=6, leading=14))
styles.add(ParagraphStyle(name="Alerta", fontSize=10, textColor=colors.HexColor("#b30000"), spaceAfter=4))
styles.add(ParagraphStyle(name="Motivo", fontSize=10, textColor=colors.HexColor("#1a6e1a"), spaceAfter=4))


def generar_informe_elegibilidad(empresa: dict, convocatoria: dict, resultado, ruta_salida: str | None = None) -> str:
    """Genera el PDF de informe de elegibilidad y devuelve la ruta del archivo."""
    if not ruta_salida:
        nombre = f"informe_{convocatoria.get('bdns_id','na')}_{empresa.get('id','na')}.pdf"
        ruta_salida = str(OUTPUT_DIR / nombre)

    doc = SimpleDocTemplate(ruta_salida, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    story = []

    story.append(Paragraph("Informe de Elegibilidad de Subvención", styles["TituloPrincipal"]))
    story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Cuerpo"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Datos de la empresa", styles["Subtitulo"]))
    tabla_empresa = [
        ["Nombre", empresa.get("nombre", "-")],
        ["CIF", empresa.get("cif", "-")],
        ["CCAA / Provincia", f"{empresa.get('ccaa','-')} / {empresa.get('provincia','-')}"],
        ["Sector", empresa.get("sector", "-")],
        ["Nº empleados", str(empresa.get("num_empleados", "-"))],
        ["PYME", "Sí" if empresa.get("es_pyme") else "No"],
    ]
    t = Table(tabla_empresa, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eef7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Convocatoria analizada", styles["Subtitulo"]))
    story.append(Paragraph(f"<b>{convocatoria.get('titulo','-')}</b>", styles["Cuerpo"]))
    story.append(Paragraph(f"Órgano: {convocatoria.get('organo','-')}", styles["Cuerpo"]))
    story.append(Paragraph(f"Ámbito: {convocatoria.get('ccaa','Nacional')}", styles["Cuerpo"]))
    story.append(Paragraph(f"Importe total convocatoria: {convocatoria.get('importe_total','-')} €", styles["Cuerpo"]))
    story.append(Paragraph(f"Plazo de solicitud: hasta {convocatoria.get('fecha_fin_solicitud','-')}", styles["Cuerpo"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Resultado del análisis", styles["Subtitulo"]))
    color_resultado = colors.HexColor("#1a6e1a") if resultado.cumple else colors.HexColor("#b30000")
    veredicto = "CUMPLE LOS REQUISITOS" if resultado.cumple else "NO CUMPLE / REVISAR"
    story.append(Paragraph(
        f'<font color="{color_resultado.hexval()}"><b>{veredicto}</b></font> — '
        f'Puntuación de compatibilidad: {resultado.puntuacion}/100',
        styles["Cuerpo"]
    ))
    story.append(Spacer(1, 8))

    if resultado.motivos:
        story.append(Paragraph("Motivos favorables:", styles["Cuerpo"]))
        for m in resultado.motivos:
            story.append(Paragraph(f"✓ {m}", styles["Motivo"]))

    if resultado.alertas:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Alertas / puntos a revisar:", styles["Cuerpo"]))
        for a in resultado.alertas:
            story.append(Paragraph(f"⚠ {a}", styles["Alerta"]))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Este informe es una orientación automatizada basada en datos públicos de la BDNS "
        "(Ministerio de Hacienda) y no sustituye la verificación de las bases reguladoras completas "
        "de la convocatoria ni el asesoramiento profesional.</i>",
        styles["Cuerpo"]
    ))

    doc.build(story)
    return ruta_salida


def generar_memoria_solicitud(empresa: dict, convocatoria: dict, respuestas: dict, ruta_salida: str | None = None) -> str:
    """
    Genera un dossier/memoria de solicitud con la documentación preparada,
    a partir de las respuestas del formulario dinámico rellenado por el usuario.
    """
    if not ruta_salida:
        nombre = f"memoria_{convocatoria.get('bdns_id','na')}_{empresa.get('id','na')}.pdf"
        ruta_salida = str(OUTPUT_DIR / nombre)

    doc = SimpleDocTemplate(ruta_salida, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    story = []

    story.append(Paragraph("Memoria de Solicitud de Subvención", styles["TituloPrincipal"]))
    story.append(Paragraph(f"Convocatoria: {convocatoria.get('titulo','-')}", styles["Subtitulo"]))
    story.append(Paragraph(f"Solicitante: {empresa.get('nombre','-')} (CIF: {empresa.get('cif','-')})", styles["Cuerpo"]))
    story.append(Spacer(1, 16))

    for seccion, contenido in respuestas.items():
        story.append(Paragraph(seccion, styles["Subtitulo"]))
        story.append(Paragraph(str(contenido), styles["Cuerpo"]))
        story.append(Spacer(1, 10))

    story.append(PageBreak())
    story.append(Paragraph("Checklist de documentación adjunta", styles["Subtitulo"]))
    checklist = [
        "Escritura de constitución / alta de autónomo",
        "NIF/CIF de la entidad",
        "Certificado de estar al corriente con Hacienda",
        "Certificado de estar al corriente con la Seguridad Social",
        "Cuentas anuales / declaración de la renta último ejercicio",
        "Memoria técnica del proyecto",
        "Presupuesto detallado",
    ]
    for item in checklist:
        story.append(Paragraph(f"☐ {item}", styles["Cuerpo"]))

    doc.build(story)
    return ruta_salida
