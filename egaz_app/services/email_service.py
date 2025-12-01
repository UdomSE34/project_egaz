# egaz_app/services/email_service.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging
from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.files.storage import default_storage

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



def send_invoice_to_both_parties(invoice, request=None):
    """
    Send invoice emails to both client and hotel with attached files
    """
    email_results = {
        'client_email_sent': False,
        'hotel_email_sent': False
    }
    
    try:
        # Use invoice_id for reference
        invoice_identifier = str(invoice.invoice_id)[:8].upper()
        
        # Prepare email for client
        client_subject = f"Invoice for {invoice.get_service_period_display()} - Ref: {invoice_identifier}"
        client_message = f"""
        Dear {invoice.client.name},
        
        Please find attached the invoice for {invoice.get_service_period_display()}.
        
        Hotel: {invoice.hotel.name}
        Service Period: {invoice.get_service_period_display()}
        Reference: {invoice_identifier}
        
        Thank you for your business!
        
        Best regards,
        Foster Investment Ltd
        """
        
        # Prepare attachments
        attachments = []
        for file_info in invoice.files:
            try:
                # Extract file path from absolute URL
                if 'media/' in file_info.get('url'):
                    file_path = file_info.get('url').split('media/')[-1]
                else:
                    file_path = file_info.get('url').split('/media/')[-1]
                
                if default_storage.exists(file_path):
                    file_content = default_storage.open(file_path).read()
                    attachments.append((file_info.get('name'), file_content, 'application/octet-stream'))
            except Exception as e:
                print(f"Error attaching file {file_info.get('name')}: {e}")
                continue
        
        # Send to client
        if invoice.client.email:
            email = EmailMessage(
                subject=client_subject,
                body=client_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invoice.client.email],
                attachments=attachments
            )
            email.send()
            email_results['client_email_sent'] = True
        
        # Send to hotel if email exists
        if invoice.hotel.email:
            hotel_subject = f"Invoice Copy - {invoice.get_service_period_display()} - Ref: {invoice_identifier}"
            hotel_message = f"""
            Dear {invoice.hotel.name},
            
            Please find attached the invoice copy for {invoice.get_service_period_display()}.
            
            Service Period: {invoice.get_service_period_display()}
            Reference: {invoice_identifier}
            
            Best regards,
            Foster Investment Ltd
            """
            
            email = EmailMessage(
                subject=hotel_subject,
                body=hotel_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invoice.hotel.email],
                attachments=attachments
            )
            email.send()
            email_results['hotel_email_sent'] = True
            
    except Exception as e:
        print(f"Error sending invoice emails: {e}")
    
    return email_results