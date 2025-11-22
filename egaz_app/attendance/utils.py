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
    
    # Convert to integers to avoid type issues
    month = int(month)
    year = int(year)
    
    days_in_month = monthrange(year, month)[1]
    created_records = []

    for day in range(1, days_in_month + 1):
        attendance_date = date(year, month, day)
        
        # Skip future dates
        if attendance_date > now.date():
            continue
            
        # Use get_or_create but handle the case properly
        obj, created = Attendance.objects.get_or_create(
            user=user,
            date=attendance_date,
            defaults={
                "status": "present", 
                "comment": "Auto-generated",
                "absent_count": 0
            }
        )
        if created:
            created_records.append(obj)
            print(f"✅ Created attendance for {user.name} on {attendance_date}")

    return created_records