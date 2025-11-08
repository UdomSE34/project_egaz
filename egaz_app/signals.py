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
        
        
