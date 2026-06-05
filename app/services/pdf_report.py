import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_payroll_pdf(breakdown: dict, title: str = "Raport wynagrodzenia") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=16, spaceAfter=20)
    elements = [
        Paragraph(title, title_style),
        Paragraph(f"Data: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    rows = [
        ["Składnik", "Kwota (PLN)"],
        ["Wynagrodzenie brutto", f"{breakdown['gross']:.2f}"],
        ["Składki ZUS pracownika", f"{breakdown['zus_employee']:.2f}"],
        ["Składka zdrowotna", f"{breakdown['health']:.2f}"],
        ["Podatek PIT", f"{breakdown['pit']:.2f}"],
        ["PPK pracownika", f"{breakdown['ppk_employee']:.2f}"],
        ["Wynagrodzenie netto", f"{breakdown['net']:.2f}"],
        ["", ""],
        ["Koszty pracodawcy", ""],
        ["ZUS pracodawcy", f"{breakdown['employer_zus']:.2f}"],
        ["Fundusz Pracy", f"{breakdown['fp']:.2f}"],
        ["FGŚP", f"{breakdown['fgszp']:.2f}"],
        ["PPK pracodawcy", f"{breakdown['ppk_employer']:.2f}"],
        ["Całkowity koszt pracodawcy", f"{breakdown['total_employer_cost']:.2f}"],
    ]
    table = Table(rows, colWidths=[10 * cm, 5 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 6), (-1, 6), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def generate_pension_pdf(result: dict, title: str = "Prognoza emerytury") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=16, spaceAfter=20)
    elements = [
        Paragraph(title, title_style),
        Paragraph(f"Data: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    rows = [
        ["Parametr", "Wartość"],
        ["Emerytura ZUS (mies.)", f"{result['zus_monthly_pension']:.2f} PLN"],
        ["Emerytura OFE (mies.)", f"{result['ofe_monthly_pension']:.2f} PLN"],
        ["Emerytura PPK (mies.)", f"{result['ppk_monthly_pension']:.2f} PLN"],
        ["Łączna emerytura (mies.)", f"{result['total_monthly_pension']:.2f} PLN"],
        ["Wiek emerytalny", str(result["retirement_age"])],
        ["Lata do emerytury", str(result["years_to_retirement"])],
        ["Kapitał ZUS", f"{result['final_zus_capital']:.2f} PLN"],
        ["Pokrycie planowanych wydatków", f"{result.get('expense_coverage', 0):.1f}%"],
    ]
    table = Table(rows, colWidths=[10 * cm, 5 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
