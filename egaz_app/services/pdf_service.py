from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO
from datetime import date, timedelta

class PdfService:
    @staticmethod
    def generate_pdf(schedules, last_two_days_only=True):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = styles['Title']
        title_style.textColor = colors.HexColor("#003366")
        title = Paragraph("Pending Schedules", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))

        today = date.today()
        yesterday = today - timedelta(days=1)
        DAY_TO_INDEX = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}

        filtered_schedules = []

        for s in schedules:
            if s.status != "Pending":
                continue

            if last_two_days_only:
                # Compute schedule date: use week_start_date if exists, else assume current week
                if s.week_start_date:
                    schedule_date = s.week_start_date + timedelta(days=DAY_TO_INDEX.get(s.day,0))
                else:
                    # fallback: assume day is in current week
                    schedule_date = today - timedelta(days=today.weekday()) + timedelta(days=DAY_TO_INDEX.get(s.day,0))

                if schedule_date in [today, yesterday]:
                    filtered_schedules.append((s, schedule_date))
            else:
                filtered_schedules.append((s, s.week_start_date or today))

        if not filtered_schedules:
            elements.append(Paragraph("No pending schedules found for the selected period.", styles['Normal']))
        else:
            data = [["Hotel", "Date", "Day", "Slot", "Status"]]
            for s, schedule_date in filtered_schedules:
                date_str = schedule_date.strftime("%Y-%m-%d") if isinstance(schedule_date, date) else str(schedule_date)
                data.append([s.hotel.name, date_str, s.day, s.slot, s.status])

            table = Table(data, colWidths=[120, 100, 80, 100, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('BOTTOMPADDING',(0,0),(-1,0),12),
                ('BACKGROUND',(0,1),(-1,-1),colors.beige),
                ('GRID',(0,0),(-1,-1),1,colors.black),
            ]))
            elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
