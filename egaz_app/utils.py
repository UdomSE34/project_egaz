from django.core.mail import send_mail

def send_alert_email(user_email, schedule):
    subject = f"Alert: Schedule Delay for {schedule.hotel.name}"
    message = f"""
    Hello,

    The scheduled collection for {schedule.hotel.name} on {schedule.day} at {schedule.end_tme} is delayed by more than 15 minutes.

    Please take necessary action.

    Thanks,
    Operations Team
    """
    send_mail(
        subject,
        message,
        'comodoosimba@gmail.com',  # From (your EMAIL_HOST_USER)
        [user_email],              # To
        fail_silently=False
    )



# Adding PaidHotelInfo creation utility
from .models import Hotel, PaidHotelInfo
from .models import PaidHotelInfo

def mark_hotel_as_paid(paid_hotel_id):
    try:
        hotel_info = PaidHotelInfo.objects.get(pk=paid_hotel_id)
        hotel_info.status = "Paid"
        hotel_info.save()
        return hotel_info
    except PaidHotelInfo.DoesNotExist:
        return None

def mark_hotel_as_unpaid(paid_hotel_id):
    try:
        hotel_info = PaidHotelInfo.objects.get(pk=paid_hotel_id)
        hotel_info.status = "Unpaid"
        hotel_info.save()
        return hotel_info
    except PaidHotelInfo.DoesNotExist:
        return None
