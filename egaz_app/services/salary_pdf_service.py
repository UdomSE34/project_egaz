# salary_pdf_service.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

def generate_salary_pdf(salaries, response):
    """
    Generate styled PDF for salaries of the current month and write it into the response object.
    """
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Filter salaries for the current month/year
    salaries = [s for s in salaries if s.month == current_month and s.year == current_year]

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Salary Report", styles['Title']))
    elements.append(Spacer(1, 6))

    # Subheading: current month and year
    current_month_year = now.strftime("%B %Y")  # Example: "September 2025"
    elements.append(Paragraph(f"Report for {current_month_year}", styles['Heading3']))
    elements.append(Spacer(1, 12))

    # Table data (headers + rows)
    data = [
        ["Name", "Role", "Base Salary", "Bonuses", "Deductions", "Total Salary", "Status"]
    ]

    for s in salaries:
        data.append([
            s.user.name,
            s.user.role,
            f"${s.base_salary:,.2f}",
            f"${s.bonuses:,.2f}",
            f"${s.deductions:,.2f}",
            f"${s.total_salary:,.2f}",
            s.status
        ])

    # Build table
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),  # header bg
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
    ]))

    elements.append(table)
    doc.build(elements)
    return response
