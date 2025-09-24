# schedules/utils.py
from datetime import datetime, timedelta
import re
from django.core.mail import send_mail 
from .models import User


def is_schedule_late(schedule):
    """
    Check if today's schedule is late by 15 minutes.
    - Only considers schedules with status 'Pending'
    - Must match today's weekday (e.g., Monday)
    - True if current time > slot end time + 15 minutes
    """
    if schedule.status != "Pending":
        return False

    # Current weekday name (e.g. "Monday")
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

    # ✅ True if now is later than allowed grace
    return now > schedule_end_with_grace


def send_schedule_alert(schedule):
    """Send email alert for late schedules of today only."""
    recipients = User.objects.filter(receive_email_notifications=True).values_list('email', flat=True)
    if not recipients:
        return

    subject = f"⚠️ Late Schedule Alert: {schedule.hotel.name}"
    message = f"""
Hello,

The schedule for {schedule.hotel.name} on {schedule.day} ({schedule.slot}) 
is delayed by more than 15 minutes.

Please take necessary action.

Thanks,
Operations Team
"""

    send_mail(
        subject,
        message,
        'comodoosimba@gmail.com',  # replace with EMAIL_HOST_USER
        list(recipients),
        fail_silently=False,
    )

# Adding PaidHotelInfo creation utility
from django.core.mail import send_mail
from django.conf import settings
import requests  # for WhatsApp API
from .models import PaidHotelInfo

# hotels/utils.py
from django.core.mail import send_mail
from django.conf import settings
from .models import PaidHotelInfo


def send_payment_email(paid_info):
    """
    Send payment confirmation email to the hotel client.
    """
    hotel = paid_info.hotel
    client_email = hotel.email
    hotel_name = hotel.name
    amount = paid_info.payment_account  # Or calculate actual amount

    if client_email:
        send_mail(
            subject=f"Payment Confirmed for {hotel_name}",
            message=(
                f"Dear {hotel_name},\n\n"
                f"Your payment has been received successfully to FOSTER INVESTMENT LTD.\n"
                f"Payment Type: {amount}\n\n"
                f"Currency Type: {hotel.currency}\n\n"
                f"Thank you for your payment we are excited to work with you.\n\n"
                f"Thank you."
                
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[client_email],
            fail_silently=True,
        )


def mark_hotel_as_paid(paid_hotel_id):
    """
    Marks a PaidHotelInfo record as Paid and sends an email notification.
    """
    try:
        hotel_info = PaidHotelInfo.objects.get(pk=paid_hotel_id)
        hotel_info.status = "Paid"
        hotel_info.save()

        # Send email notification
        send_payment_email(hotel_info)
        return hotel_info
    except PaidHotelInfo.DoesNotExist:
        return None


def mark_hotel_as_unpaid(paid_hotel_id):
    """
    Marks a PaidHotelInfo record as Unpaid.
    """
    try:
        hotel_info = PaidHotelInfo.objects.get(pk=paid_hotel_id)
        hotel_info.status = "Unpaid"
        hotel_info.save()
        return hotel_info
    except PaidHotelInfo.DoesNotExist:
        return None



# schedules/utils.py
from datetime import datetime
from django.core.mail import send_mail
from .models import Schedule
import logging

logger = logging.getLogger(__name__)

def send_daily_apology_emails():
    """Send apology emails to hotels if schedule is pending today at 16:00+."""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute

    # Only run if time is 16:00 or later
    if current_hour < 16:
        logger.info("It's not 16:00 yet. Skipping apology emails.")
        return

    today_day_name = now.strftime('%A')  # e.g., 'Monday'

    # Get all pending schedules for today
    pending_schedules = Schedule.objects.filter(status="Pending", day=today_day_name)
    if not pending_schedules.exists():
        logger.info("No pending schedules for today. Nothing to send.")
        return

    sent_count = 0
    for schedule in pending_schedules:
        hotel = schedule.hotel

        if not hotel.email:
            logger.warning(f"No email found for hotel {hotel.name}. Skipping.")
            continue

        subject = f"Apology for delay in waste collection at {hotel.name}"
        message = (
            f"Dear {hotel.name} Team,\n\n"
            f"We apologize for the delay in collecting waste scheduled for {schedule.day} ({schedule.slot}). "
            "We are aware of the pending status and will come tomorrow to complete the collection.\n\n"
            "Thank you for your understanding.\n"
            "Best regards,\nYour Waste Management Team"
        )

        try:
            send_mail(
                subject,
                message,
                'comodoosimba@gmail.com',  # Replace with EMAIL_HOST_USER
                [hotel.email],
                fail_silently=False
            )
            sent_count += 1
            logger.info(f"Apology email sent to hotel '{hotel.name}' ({hotel.email})")
        except Exception as e:
            logger.error(f"Failed to send email to hotel '{hotel.name}': {e}")

    logger.info(f"Total apology emails sent: {sent_count}")
