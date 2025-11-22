from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Schedule, Alert, User
from django.core.mail import send_mail
from datetime import datetime, timedelta
import re

def is_schedule_late(schedule):
    """
    Check if the schedule is late by 15 minutes ONLY for today's day.
    """
    if schedule.status != "Pending":
        return False

    # Check current weekday (e.g., "Monday")
    today_day = datetime.now().strftime("%A")
    if schedule.day != today_day:
        return False

    # Parse slot "HH:MM – HH:MM"
    match = re.match(r"(\d{2}:\d{2})\s*–\s*(\d{2}:\d{2})", schedule.slot)
    if not match:
        return False

    end_time_str = match.group(2)
    end_time = datetime.strptime(end_time_str, "%H:%M").time()

    now = datetime.now()
    schedule_end_with_grace = datetime.combine(now.date(), end_time) + timedelta(minutes=15)

    return now > schedule_end_with_grace


@receiver(post_save, sender=Schedule)
def create_alert_for_schedule(sender, instance, created, **kwargs):
    """Create an alert if the schedule is late without changing its status."""
    if instance.status == "Pending" and is_schedule_late(instance):
        # Do NOT change the status
        Alert.objects.create(
            schedule=instance,
            alert_type='Late_Service',
            severity='Critical'
        )

@receiver(post_save, sender=Alert)
def alert_email(sender, instance, created, **kwargs):
    """Send email alert to all users who opted in for notifications."""
    if created:
        schedule = instance.schedule
        # Get all users who want to receive notifications
        recipients = User.objects.filter(receive_email_notifications=True).values_list('email', flat=True)
        if not recipients:
            return

        subject = f"⚠️ Alert: {schedule.hotel.name} Schedule is Late"
        message = f"""
Hello,

The schedule for {schedule.hotel.name} on {schedule.day} at {schedule.slot} is delayed by more than 15 minutes.

Please take necessary action.

Thanks,
Operations Team
"""
        send_mail(
            subject,
            message,
            'comodoosimba@gmail.com',  # From email
            list(recipients),
            fail_silently=False
        )


# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from datetime import date
from .models import Hotel, PaidHotelInfo

@receiver(post_save, sender=Hotel)
def create_paid_hotel_info(sender, instance, created, **kwargs):
    if created:
        today = now().date()
        first_day_of_month = date(today.year, today.month, 1)

        # Create a PaidHotelInfo for the current month
        PaidHotelInfo.objects.get_or_create(
            hotel=instance,
            month=first_day_of_month,
            defaults={
                "name": instance.name,
                "address": instance.address,
                "contact_phone": instance.contact_phone,
                "hadhi": instance.hadhi,
                "currency": instance.currency,
                "payment_account": instance.payment_account,
                "status": "Unpaid",
            }
        )
        
        
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Hotel, Invoice, Client

@receiver(post_save, sender=Hotel)
def create_invoice_for_new_hotel(sender, instance, created, **kwargs):
    if created:
        # Hapa unachagua client default au logic ya client
        default_client = Client.objects.first()  # Mfano
        Invoice.objects.create(
            hotel=instance,
            client=default_client,
            amount=0.0,
            status='not_sent',
            month=datetime.now().month,
            year=datetime.now().year,
            comment='Auto-generated invoice for new hotel'
        )


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import User, Attendance, Salary, RoleSalaryPolicy
from datetime import timedelta

@receiver(post_save, sender=User)
def create_salary_for_new_user(sender, instance, created, **kwargs):
    """
    Automatically create salary record for new active users
    """
    if created and instance.is_active and instance.role != "Admin":
        print(f"💰 Creating salary for new user: {instance.name} ({instance.role})")
        
        # Get the role policy
        policy = RoleSalaryPolicy.objects.filter(role=instance.role).first()
        
        if policy:
            # Create salary for current month
            current_month = timezone.now().month
            current_year = timezone.now().year
            
            salary, salary_created = Salary.objects.get_or_create(
                user=instance,
                month=current_month,
                year=current_year,
                defaults={
                    "policy": policy,
                    "base_salary": policy.base_salary,
                    "bonuses": policy.bonuses,
                    "deductions": 0,
                    "total_salary": policy.base_salary + policy.bonuses,
                    "status": "Unpaid"
                }
            )
            
            if salary_created:
                print(f"✅ Salary created for {instance.name}: {salary.salary_id}")
            else:
                print(f"📝 Salary already exists for {instance.name}")
        else:
            print(f"⚠️ No policy found for role: {instance.role} - Cannot create salary")

@receiver(post_save, sender=User)
def create_attendance_for_new_user(sender, instance, created, **kwargs):
    """
    Automatically create attendance records for new active users
    """
    if created and instance.is_active:
        print(f"🎯 Creating attendance for new user: {instance.name}")
        
        # Create attendance for today and a few days back
        today = timezone.now().date()
        
        # Create attendance for current week (7 days back and 3 days forward)
        for days_back in range(7, -4, -1):  # From 7 days ago to 3 days in future
            attendance_date = today - timedelta(days=days_back)
            
            # Don't create records too far in the future
            if attendance_date > today + timedelta(days=3):
                continue
                
            # Create attendance record if it doesn't exist
            Attendance.objects.get_or_create(
                user=instance,
                date=attendance_date,
                defaults={
                    "status": "present",  # Default to present
                    "comment": "Auto-created for new user",
                    "absent_count": 0
                }
            )