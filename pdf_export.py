from fpdf import FPDF
import pandas as pd
from typing import List
import tempfile, os

DAYS_ORDER = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
SHIFTS     = ["בוקר", "ערב", "לילה"]

SHIFT_HOURS = {
    "בוקר":    "07:00-15:00",
    "בוקר 12": "07:00-19:00",
    "ערב":     "15:00-23:00",
    "לילה":    "23:00-07:00",
    "לילה 12": "19:00-07:00",
}


def export_pdf(df: pd.DataFrame, week_label: str, notes: str = "") -> str:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()

    # פונט שתומך בעברית – נשתמש ב-Helvetica כברירת מחדל
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_fill_color(232, 228, 248)
    pdf.cell(0, 12, f"Work Schedule - {week_label}", ln=True, align="C", fill=True)
    pdf.ln(3)

    if notes:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, f"Notes: {notes}", ln=True, align="C")
        pdf.ln(2)

    # טבלה
    col_w = 35
    row_h = 22
    day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    shift_labels = {"בוקר": "Morning", "ערב": "Evening", "לילה": "Night"}
    shift_colors = {
        "בוקר": (212, 236, 212),
        "ערב":  (253, 232, 200),
        "לילה": (217, 212, 240),
    }

    # כותרות
    pdf.set_font("Helvetica", "B", 11)
    for label in day_labels:
        pdf.cell(col_w, 10, label, border=1, align="C")
    pdf.ln()

    # שורות משמרת
    for shift in SHIFTS:
        hours = SHIFT_HOURS[shift]
        agents_per_day = []
        for day in DAYS_ORDER:
            agents = df[df[day] == shift]["שם"].tolist()
            agents_per_day.append(agents)

        max_agents = max(len(a) for a in agents_per_day) if agents_per_day else 1
        cell_h = max(row_h, max_agents * 7 + 10)

        r, g, b = shift_colors[shift]
        pdf.set_fill_color(r, g, b)
        pdf.set_font("Helvetica", "B", 9)

        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for i, agents in enumerate(agents_per_day):
            x = x_start + i * col_w
            pdf.set_xy(x, y_start)
            pdf.set_font("Helvetica", "B", 8)
            shift_en = shift_labels[shift]
            text = f"{shift_en}\n{hours}\n" + "\n".join(agents) if agents else f"{shift_en}\n{hours}\n—"
            pdf.multi_cell(col_w, cell_h / (len(text.split("\n")) + 1),
                           text, border=1, align="C", fill=True)

        pdf.set_xy(x_start, y_start + cell_h)
        pdf.ln(0)

    # שמור לקובץ זמני
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name