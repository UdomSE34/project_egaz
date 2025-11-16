# egaz_app/services/email_service.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_service_period_display(month, year):
    """Get service period for next month"""
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    next_month_name = datetime(next_year, next_month, 1).strftime('%B')
    return f"{next_month_name} {next_year}"

def get_due_date():
    """Calculate due date (7 days from now)"""
    due_date = datetime.now() + timedelta(days=7)
    return due_date.strftime('%d %b %Y')

def send_invoice_email(invoice, recipient_type='client'):
    """
    Send invoice notification email to client or hotel
    recipient_type: 'client' or 'hotel'
    """
    try:
        hotel = invoice.hotel
        client = invoice.client
        
        if recipient_type == 'client':
            recipient_email = client.email
            recipient_name = client.name
        else:  # hotel
            recipient_email = hotel.email
            recipient_name = hotel.name

        if not recipient_email:
            logger.warning(f"No email found for {recipient_type}: {recipient_name}")
            return False

        # Email subject
        subject = f"Invoice Notification - {invoice.invoice_number}"

        # Email context
        context = {
            'invoice': invoice,
            'recipient_name': recipient_name,
            'recipient_type': recipient_type,
            'hotel': hotel,
            'client': client,
            'invoice_number': invoice.invoice_number,
            'amount': invoice.amount,
            'service_period': get_service_period_display(invoice.month, invoice.year),
            'due_date': get_due_date(),
        }

        # Render HTML email template
        html_content = render_to_string('emails/invoice_notification.html', context)
        text_content = strip_tags(html_content)  # Fallback text version

        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
            reply_to=['info@fosterinvestment.co.uk']
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"Invoice email sent to {recipient_type}: {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send invoice email: {str(e)}")
        return False

def send_invoice_to_both_parties(invoice):
    """
    Send invoice notifications to both client and hotel
    """
    client_sent = send_invoice_email(invoice, 'client')
    hotel_sent = send_invoice_email(invoice, 'hotel')
    
    return {
        'client_email_sent': client_sent,
        'hotel_email_sent': hotel_sent
    }