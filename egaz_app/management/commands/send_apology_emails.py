# schedules/management/commands/send_apology_emails.py
from django.core.management.base import BaseCommand
from egaz_app.utils import send_daily_apology_emails

class Command(BaseCommand):
    help = "Send apology emails for today's pending schedules"

    def handle(self, *args, **kwargs):
        send_daily_apology_emails()
