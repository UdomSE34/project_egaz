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
