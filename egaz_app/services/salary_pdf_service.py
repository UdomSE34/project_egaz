# salary_pdf_service.py
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from datetime import datetime
from django.db.models import Count, Q
from egaz_app.models import Attendance

def generate_salary_pdf(salaries, response):
    """
    Generate styled PDF for salaries of the current month and write it into the response object.
    Only include active users. Absences are dynamically fetched from Attendance table.
    """
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Filter salaries for the current month/year and only active users
    salaries = [s for s in salaries if s.month == current_month and s.year == current_year and s.user.status.lower() == "active"]

    # Use landscape mode for wider table
    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()

    # Add custom style for wrapping long text
    wrap_style = ParagraphStyle(name="wrap", fontSize=10, leading=12)

    # Title
    elements.append(Paragraph("Salary Report", styles['Title']))
    elements.append(Spacer(1, 6))

    # Subheading: current month and year
    current_month_year = now.strftime("%B %Y")
    elements.append(Paragraph(f"Report for {current_month_year}", styles['Heading3']))
    elements.append(Spacer(1, 12))

    # Table headers
    data = [
        ["Name", "Role", "Base Salary", "Bonuses", "Deductions", "Total Salary", "Absences", "Status"]
    ]

    total_payroll = 0
    total_absences = 0

    for s in salaries:
        # Get absences from Attendance table
        absences = Attendance.objects.filter(
            user=s.user,
            status="absent",
            date__month=current_month,
            date__year=current_year
        ).count()

        data.append([
            Paragraph(s.user.name, wrap_style),
            Paragraph(s.user.role, wrap_style),
            f"${s.base_salary:,.2f}",
            f"${s.bonuses:,.2f}",
            f"${s.deductions:,.2f}",
            f"${s.total_salary:,.2f}",
            absences,
            Paragraph(s.user.status.capitalize(), wrap_style)
        ])

        total_payroll += s.total_salary
        total_absences += absences

    # Add summary row
    data.append([
        "TOTAL",
        "",
        "",
        "",
        "",
        f"${total_payroll:,.2f}",
        total_absences,
        ""
    ])

    # Adjust column widths to fit
    col_widths = [5*cm, 3*cm, 3*cm, 3*cm, 3*cm, 3*cm, 2*cm, 3*cm]

    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0e0e0")),
    ]))

    elements.append(table)
    doc.build(elements)
    return response
