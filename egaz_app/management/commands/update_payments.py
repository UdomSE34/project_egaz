from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import date
from egaz_app.models import Hotel, PaidHotelInfo, Notification
from django.core.mail import send_mail

class Command(BaseCommand):
    help = "Daily job: ensure monthly unpaid records exist & send reminders on 27th"

    def handle(self, *args, **kwargs):
        today = now().date()
        first_day_of_month = date(today.year, today.month, 1)

        # 1️⃣ Ensure every hotel has an 'Unpaid' record for this month
        created_count = 0
        for hotel in Hotel.objects.all():
            obj, created = PaidHotelInfo.objects.get_or_create(
                hotel=hotel,
                month=first_day_of_month,
                defaults={
                    "name": hotel.name,
                    "address": hotel.address,
                    "contact_phone": hotel.contact_phone,
                    "hadhi": hotel.hadhi,
                    "currency": hotel.currency,
                    "payment_account": hotel.payment_account,
                    "status": "Unpaid",
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Created unpaid record for {hotel.name}"))

        self.stdout.write(self.style.SUCCESS(
            f"Total new monthly records created: {created_count}"
        ))

        # 2️⃣ Reminder block (only runs on 27th)
        if today.day == 27:
            self.stdout.write(self.style.NOTICE("📣 Today is 27th — sending reminders for unpaid hotels"))

            unpaid_hotels = PaidHotelInfo.objects.filter(
                month=first_day_of_month,
                status="Unpaid"
            )

            reminder_count = 0
            for record in unpaid_hotels:
                client_user = getattr(record.hotel.client, "user", None)
                hotel_email = record.hotel.email

                # Create in-system notification
                if client_user:
                    notif = Notification.objects.create(
                        recipient=client_user,
                        message=f"Hello {record.name}, this is a polite reminder to complete your payment for {today.strftime('%B %Y')} before the end of this month. Thank you!"
                    )
                    self.stdout.write(self.style.NOTICE(f"🔔 Notification created for {record.name}"))

                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ No client user for hotel {record.name}"))

                # Send email
                if hotel_email:
                    try:
                        send_mail(
                            subject="Monthly Payment Reminder",
                            message=(
                                f"Dear {record.name},\n\n"
                                f"We hope you are doing well. This is a friendly reminder that your payment for {today.strftime('%B %Y')} "
                                f"is due before the end of this month.\n\n"
                                "We truly appreciate your timely cooperation and support.\n\n"
                                "Best regards,\n"
                                "The Waste Management Team"
                            ),
                            from_email="comodoosimba@gmail.com",
                            recipient_list=[hotel_email],
                            fail_silently=False,  # temporarily set to False to catch email errors
                        )
                        self.stdout.write(self.style.NOTICE(f"📧 Email sent to {hotel_email}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Failed to send email to {hotel_email}: {e}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ No email for hotel {record.name}"))

                reminder_count += 1

            self.stdout.write(self.style.SUCCESS(f"Total reminders sent: {reminder_count}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Today is {today.day}, not 27th — skipping reminders"))

