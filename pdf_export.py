from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import tempfile
import pandas as pd

DAYS_ORDER = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
SHIFTS     = ["בוקר", "ערב", "לילה"]
SHIFT_HOURS = {
    "בוקר": "07:00-15:00",
    "ערב":  "15:00-23:00",
    "לילה": "23:00-07:00",
}
SHIFT_COLORS = {
    "בוקר": colors.HexColor("#d4ecd4"),
    "ערב":  colors.HexColor("#fde8c8"),
    "לילה": colors.HexColor("#d9d4f0"),
}


def export_pdf(df: pd.DataFrame, week_label: str, notes: str = "") -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=landscape(A4),
        rightMargin=10*mm, leftMargin=10*mm,
        topMargin=10*mm, bottomMargin=10*mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # כותרת
    title_style = ParagraphStyle("title", fontSize=16, alignment=1, spaceAfter=6)
    elements.append(Paragraph(f"Work Schedule - {week_label}", title_style))
    if notes:
        note_style = ParagraphStyle("note", fontSize=10, alignment=1, spaceAfter=6)
        elements.append(Paragraph(notes, note_style))
    elements.append(Spacer(1, 5*mm))

    # בניית טבלה
    day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    shift_en   = {"בוקר": "Morning", "ערב": "Evening", "לילה": "Night"}

    header = [""] + day_labels
    data   = [header]

    style_commands = [
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8e4f8")),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.HexColor("#3d3d5c")),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",   (0,0), (-1,0),  "Helvetica-Bold"),
    ]

    for row_idx, shift in enumerate(SHIFTS, start=1):
        row = [f"{shift_en[shift]}\n{SHIFT_HOURS[shift]}"]
        for day in DAYS_ORDER:
            agents = df[df[day] == shift]["שם"].tolist()
            row.append("\n".join(agents) if agents else "—")

        data.append(row)
        bg = SHIFT_COLORS[shift]
        style_commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))
        style_commands.append(("FONTNAME", (0, row_idx), (0, row_idx), "Helvetica-Bold"))

    col_widths = [30*mm] + [33*mm]*7
    table = Table(data, colWidths=col_widths, rowHeights=25*mm)
    table.setStyle(TableStyle(style_commands))
    elements.append(table)

    doc.build(elements)
    return tmp.name