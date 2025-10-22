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
from django.utils.html import format_html


def send_payment_email(paid_info):
    """
    Send a styled payment confirmation email (like an invoice) to the hotel client.
    """
    hotel = paid_info.hotel
    client_email = hotel.email
    if not client_email:
        return

    subject = f"Payment Confirmation - {hotel.name}"

    # Plain text fallback
    plain_message = (
        f"Dear {hotel.name},\n\n"
        f"Your payment has been received successfully to FOSTER INVESTMENT LTD.\n\n"
        f"Here are your payment details:\n"
        f"Name: {paid_info.name}\n"
        f"Address: {paid_info.address}\n"
        f"Contact: {paid_info.contact_phone}\n"
        f"Hadhi: {paid_info.hadhi}\n"
        f"Currency: {paid_info.currency}\n"
        f"Account: {paid_info.payment_account}\n"
        f"Month: {paid_info.month.strftime('%B %Y')}\n"
        f"Status: {paid_info.status}\n\n"
        f"Thank you for trusting us.\n\n"
        f"FOSTER INVESTMENT LTD"
    )

    # HTML styled message
    html_message = f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #2E86C1;">Payment Confirmation</h2>
        <p>Dear <strong>{hotel.name}</strong>,</p>
        <p>We are pleased to confirm that your payment has been successfully received by 
        <strong>FOSTER INVESTMENT LTD</strong>. Below are the details of your transaction:</p>

        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; background: #f4f6f7;">Name</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paid_info.name}</td>
            </tr>
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; background: #f4f6f7;">Address</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paid_info.address}</td>
            </tr>
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; background: #f4f6f7;">Contact</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paid_info.contact_phone}</td>
            </tr>
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; background: #f4f6f7;">Hadhi</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paid_info.hadhi}</td>
            </tr>
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; background: #f4f6f7;">Currency</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paid_info.currency}</td>
            </tr>
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; background: #f4f6f7;">Account</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paid_info.payment_account}</td>
            </tr>
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; background: #f4f6f7;">Month</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paid_info.month.strftime('%B %Y')}</td>
            </tr>
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; background: #f4f6f7;">Status</th>
                <td style="border: 1px solid #ddd; padding: 8px; color: {'green' if paid_info.status == 'Paid' else 'red'};">
                    <strong>{paid_info.status}</strong>
                </td>
            </tr>
        </table>

        <p style="margin-top: 20px;">Thank you for your payment. We are excited to continue working with you.</p>
        <p>Best regards, <br><strong>FOSTER INVESTMENT LTD</strong></p>
    </div>
    """

    send_mail(
        subject,
        plain_message,  # plain text version
        settings.DEFAULT_FROM_EMAIL,
        [client_email],
        html_message=html_message,
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
from datetime import datetime, timedelta
from django.core.mail import send_mail
from .models import Schedule
import logging

logger = logging.getLogger(__name__)

def send_apology_email(schedule, day_label="today"):
    """
    Send an apology email for a single schedule.
    `day_label` is used in the message: "today" or "tomorrow".
    Returns True if email was sent, False otherwise.
    """
    hotel = schedule.hotel
    if not hotel.email:
        logger.warning(f"No email found for hotel {hotel.name}. Skipping.")
        return False

    subject = f"Apology for delay in waste collection at {hotel.name}"
    message = (
        f"Dear {hotel.name} Team,\n\n"
        f"We apologize for the delay in collecting waste scheduled for {schedule.day} ({schedule.slot}). "
        f"We are aware of the pending status and will come {day_label} to complete the collection.\n\n"
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
        logger.info(f"{day_label.capitalize()} email sent to '{hotel.name}' ({hotel.email})")
        return True
    except Exception as e:
        logger.error(f"Failed to send {day_label} email to hotel '{hotel.name}': {e}")
        return False


def send_daily_apology_emails():
    """
    Send apology emails for pending schedules:
    - today if time >= 16:00
    - tomorrow messages can also be sent via API or scheduled task
    Returns a dict with counts and hotel names.
    """
    now = datetime.now()
    current_hour = now.hour

    if current_hour < 16:
        logger.info("It's not 16:00 yet. Skipping apology emails.")
        return {"today_sent": 0, "today_hotels": []}

    today_name = now.strftime('%A')
    tomorrow_name = (now + timedelta(days=1)).strftime('%A')

    results = {"today_sent": 0, "today_hotels": [], "tomorrow_sent": 0, "tomorrow_hotels": []}

    # Send today's apology emails
    pending_today = Schedule.objects.filter(status="Pending", day=today_name)
    for schedule in pending_today:
        if send_apology_email(schedule, "today"):
            results["today_sent"] += 1
            results["today_hotels"].append(schedule.hotel.name)

    # Send tomorrow's apology emails
    pending_tomorrow = Schedule.objects.filter(status="Pending", day=tomorrow_name)
    for schedule in pending_tomorrow:
        if send_apology_email(schedule, "tomorrow"):
            results["tomorrow_sent"] += 1
            results["tomorrow_hotels"].append(schedule.hotel.name)

    logger.info(f"Apology emails sent today: {results['today_sent']}, tomorrow: {results['tomorrow_sent']}")
    return results


from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string


def send_html_email(subject, to_email, template_name, context):
    """
    Reusable helper for sending HTML + plain text emails.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    html_content = render_to_string(template_name, context)
    text_content = render_to_string("emails/plain_text_fallback.txt", context)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


def send_hotel_created_email(hotel):
    """
    1️⃣ Sent when a new PendingHotel is created.
    """
    if not hotel.email:
        return

    subject = f"Hotel Registration Received: {hotel.name}"
    context = {
        "title": "Hotel Registration Received",
        "hotel_name": hotel.name,
        "address": hotel.address,
        "contact": hotel.contact_phone,
        "status": hotel.status,
        "message": (
            "We have received your hotel registration request. "
            "Our team will review your information and get back to you soon."
        ),
    }
    text_content = "This is an automated notification from FOSTER INVESTMENT LTD."

    send_html_email(subject, hotel.email, "emails/hotel_created.html", context)


def send_hotel_approved_email(hotel):
    """
    2️⃣ Sent when the hotel is approved and moved to main Hotel table.
    """
    if not hotel.email:
        return

    subject = f"Hotel Approved: {hotel.name}"
    context = {
        "title": "Hotel Approval Confirmation",
        "hotel_name": hotel.name,
        "address": hotel.address,
        "contact": hotel.contact_phone,
        "hadhi": hotel.hadhi,
        "currency": hotel.currency,
        "message": (
            "Congratulations! Your hotel registration has been approved. "
            "You can now access all related services through our system."
        ),
    }
    send_html_email(subject, hotel.email, "emails/hotel_approved.html", context)


def send_hotel_rejected_email(hotel):
    """
    3️⃣ Sent when the hotel is rejected.
    """
    if not hotel.email:
        return

    subject = f"Hotel Application Rejected: {hotel.name}"
    context = {
        "title": "Hotel Application Update",
        "hotel_name": hotel.name,
        "address": hotel.address,
        "contact": hotel.contact_phone,
        "message": (
            "We regret to inform you that your hotel registration request has been rejected. "
            "You may review your information and apply again if you wish."
        ),
    }
    send_html_email(subject, hotel.email, "emails/hotel_rejected.html", context)
