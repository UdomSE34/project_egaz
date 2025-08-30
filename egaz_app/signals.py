from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Schedule, Alert
from django.core.mail import send_mail
from django.utils import timezone

@receiver(post_save, sender=Schedule)
def create_alert_for_schedule(sender, instance, created, **kwargs):
    if created:
        Alert.objects.create(
            schedule=instance,
            alert_type='Late_Service',
            severity='Critical'
        )

@receiver(post_save, sender=Alert)
def alert_email(sender, instance, created, **kwargs):
    if created:
        schedule = instance.schedule
        user_email = "comodoosimba@example.com"  # Replace with real email
        subject = f"Alert: {schedule.hotel.name} is Late"
        message = f"The schedule on {schedule.day} at {schedule.end_time} is delayed."
        
        send_mail(
            subject,
            message,
            'comodoosimba@gmail.com',
            [user_email],
            fail_silently=False
        )
