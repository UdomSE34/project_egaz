from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO
from datetime import date, timedelta

class PdfService:
    @staticmethod
    def generate_pdf(schedules):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph("Pending Schedules", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Mapping weekdays to index
        DAY_TO_INDEX = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
            'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
        }

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Filter schedules: only Pending and for today/yesterday
        filtered = []
        for s in schedules:
            if s.status != "Pending":
                continue
            if s.week_start_date and s.day in DAY_TO_INDEX:
                schedule_date = s.week_start_date + timedelta(days=DAY_TO_INDEX[s.day])
                if schedule_date in [today, yesterday]:
                    filtered.append((s, schedule_date))

        if not filtered:
            elements.append(Paragraph("No pending schedules found for Today or Yesterday.", styles['Normal']))
        else:
            data = [["Hotel", "Date", "Day", "Status"]]
            for schedule, schedule_date in filtered:
                data.append([
                    schedule.hotel.name,                       # Hotel name
                    schedule_date.strftime("%Y-%m-%d"),        # Date
                    schedule_date.strftime("%A"),              # Day name
                    schedule.status,                           # Status
                ])

            table = Table(data, colWidths=[120, 100, 100, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
