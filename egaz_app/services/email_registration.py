from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

# Configure logger (if not already)
logger = logging.getLogger(__name__)

def send_registration_email(client):
    """
    Send registration confirmation email to client.
    Fail gracefully if email cannot be sent.
    """
    subject = 'Welcome to Foster Investment - Registration Successful'
    
    # HTML email content
    html_message = render_to_string('emails/registration_confirmation.html', {
        'client_name': client.name,
        'company_name': 'Foster Investment'
    })
    
    # Plain text fallback
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[client.email],
            html_message=html_message,
            fail_silently=False,  # still raises exception
        )
        return True
    except Exception as e:
        # Log the error instead of failing
        logger.error(f"Failed to send registration email to {client.email}: {e}")
        print(f"Failed to send registration email to {client.email}: {e}")
        return False
