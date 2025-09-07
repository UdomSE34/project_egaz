# attendance/utils.py
from datetime import date, timedelta
from calendar import monthrange
from django.utils import timezone
from egaz_app.models import Attendance, User

def ensure_attendance_for_month(user, month=None, year=None):
    """
    Ensure that the user has attendance records for all days in the given month.
    Automatically marks as 'present' if no record exists.
    """
    now = timezone.now()
    month = month or now.month
    year = year or now.year
    days_in_month = monthrange(year, month)[1]

    created_records = []

    for day in range(1, days_in_month + 1):
        attendance_date = date(year, month, day)
        obj, created = Attendance.objects.get_or_create(
            user=user,
            date=attendance_date,
            defaults={"status": "present", "comment": ""}
        )
        if created:
            created_records.append(obj)

    return created_records
