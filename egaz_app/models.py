from django.db import models
import uuid
from django.conf import settings
from django.utils.timezone import now  # <-- add this
import secrets
from datetime import date, timedelta
from django.contrib.auth.hashers import  check_password




# Client
class Client(models.Model):
    ROLE_CHOICES = [
        ('client', 'Client'),
    ]

    client_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    address = models.TextField()
    password = models.CharField(max_length=255)  # hashed password will be stored
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client', editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Hash the password before saving if it's not already hashed
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.role})"
    

# Hotels
class Hotel(models.Model):
    HOTEL_TYPES = [
        ('Hotel', 'Hotel'),
        ('Villa', 'Villa'),
        ('Guest_House', 'Guest House'),
        ('Restaurant', 'Restaurant'),
    ]

    PAYMENT_CURRENCY = [
        ('USD', 'USD'),
        ('TZS', 'TZS'),
    ]
    
    hotel_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
    'Client',
    on_delete=models.CASCADE,
    related_name='hotel',
    null=True,
    blank=True
)

    name = models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20)
    
    collection_frequency = models.CharField(max_length=50, default="daily")
    total_rooms = models.IntegerField(default=0)
    type = models.CharField(max_length=50, default="hotel")
    waste_per_day = models.IntegerField(default=0)
    currency = models.CharField(max_length=10, default="TZS")
    payment_account = models.CharField(max_length=100, default="N/A")
    hadhi = models.CharField(max_length=50, default="normal")

    created_at = models.DateTimeField(auto_now_add=True)

# Pending Hotles
class PendingHotel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
    'Client',
    on_delete=models.CASCADE,
    related_name='pending_hotel',
    null=True,
    blank=True
)

    name = models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20)
    hadhi = models.CharField(max_length=50)
    total_rooms = models.IntegerField(default=0)
    type = models.CharField(max_length=50)
    waste_per_day = models.IntegerField(default=0)
    collection_frequency = models.CharField(max_length=50, default="daily")
    currency = models.CharField(max_length=10, default="TZS")
    payment_account = models.CharField(max_length=100, default="N/A")
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    
# Users
import uuid
from django.db import models
from django.contrib.auth.hashers import make_password

class User(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password_hash = models.TextField()

    # Extra details
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)

    RELATIONSHIP_CHOICES = [
        ("baba", "Baba"),
        ("mama", "Mama"),
        ("kaka", "Kaka"),
        ("dada", "Dada"),
        ("babu", "Babu"),
        ("bibi", "Bibi"),
        ("other", "Other"),
    ]
    emergency_contact_relationship = models.CharField(
        max_length=20, choices=RELATIONSHIP_CHOICES, null=True, blank=True
    )
    emergency_contact_phone = models.CharField(max_length=20, null=True, blank=True)

    # Updated roles
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('HR', 'HR'),
        ('Supervisors', 'Supervisors'),
        ('Drivers', 'Drivers'),
        ('Staff', 'Staff'),
        ('Workers', 'Workers'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Workers')
    suspend_comment = models.TextField(null=True, blank=True)
    delete_comment = models.TextField(null=True, blank=True)
    finaldelete_comment = models.TextField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("pending_suspend", "Pending Suspend"),
            ("pending_delete", "Pending Delete"),
            ("suspended", "Suspended"),
            ("deleted", "Deleted"),
        ],
        default="active"
    )
    is_active = models.BooleanField(default=True)
    receive_email_notifications = models.BooleanField(default=False)  # new field
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.password_hash or not self.password_hash.startswith('pbkdf2_'):
            self.password_hash = make_password(self.password_hash or "123456")
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return f"{self.name} ({self.role})"

# Waste Types
class WasteType(models.Model):
    waste_type_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    standard_duration = models.DurationField(null=True, blank=True)

# Vehicles
class Vehicle(models.Model):
    vehicle_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration_number = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=50)
    capacity = models.CharField(max_length=50)
    current_status = models.CharField(max_length=20, choices=[('Available','Available'),('In_Use','In_Use'),('Maintenance','Maintenance')])
    last_maintenance_date = models.DateField(null=True, blank=True)

# Teams
class Team(models.Model):
    team_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_teams')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# Work Shifts
class WorkShift(models.Model):
    shift_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    shift_date = models.DateField()
    scheduled_start_time = models.DateTimeField()
    scheduled_end_time = models.DateTimeField()
    shift_type = models.CharField(max_length=20, choices=[('Morning','Morning'),('Evening','Evening'),('Night','Night')])

class Schedule(models.Model):
    STATUS_CHOICES = [
        ('Pending','Pending'),
        ('In_Progress','In Progress'),
        ('Completed','Completed'),
    ]

    SLOT_CHOICES = [
        ("06:00 – 12:00", "Morning (06:00 – 12:00)"),
        ("06:00 – 18:00", "Afternoon (00:30 – 18:00)"),
    ]

    DAYS_OF_WEEK = [
        ('Monday','Monday'), ('Tuesday','Tuesday'), ('Wednesday','Wednesday'),
        ('Thursday','Thursday'), ('Friday','Friday'), ('Saturday','Saturday'), ('Sunday','Sunday')
    ]

    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    day = models.CharField(max_length=50, choices=DAYS_OF_WEEK)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    
    # NEW FIELD: Show schedule to user
    is_visible = models.BooleanField(default=False, help_text="Check if this schedule should be visible to users")

    slot = models.CharField(max_length=20, choices=SLOT_CHOICES, default="Morning")

    hotel = models.ForeignKey("Hotel", on_delete=models.CASCADE, related_name="schedules")
    completion_notes = models.TextField(blank=True, null=True)
    week_start_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['week_start_date', 'day', 'slot']
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'

    def __str__(self):
        return f"{self.hotel.name} - {self.day} ({self.slot}) - {self.status}"

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

class Notification(models.Model):
    STATUS_CHOICES = [
        ('Unread', 'Unread'),
        ('Read', 'Read'),
        ('Acknowledged', 'Acknowledged')
    ]

    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Sender (User or Client)
    sender_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name='sent_notifications'
    )
    sender_object_id = models.UUIDField()
    sender = GenericForeignKey('sender_content_type', 'sender_object_id')

    # Recipient (User or Client). Null = broadcast
    recipient_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name='received_notifications',
        null=True, blank=True
    )
    recipient_object_id = models.UUIDField(null=True, blank=True)
    recipient = GenericForeignKey('recipient_content_type', 'recipient_object_id')

    message_content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Unread')
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_time']

    def __str__(self):
        sender_name = getattr(self.sender, 'name', 'Unknown Sender')
        recipient_name = getattr(self.recipient, 'name', 'Broadcast')
        return f"{sender_name} → {recipient_name}: {self.message_content[:30]}..."


# Alerts
class Alert(models.Model):
    alert_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=[('Late_Service','Late_Service')])
    severity = models.CharField(max_length=20, choices=[('Critical','Critical')])
    
    
class CompletedWasteRecord(models.Model):
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ✅ link to schedule
    schedule = models.ForeignKey("Schedule", on_delete=models.CASCADE, related_name="completed_wastes")

    # ✅ only the requested fields
    waste_type = models.CharField(max_length=100)       # e.g., Organic, Plastic
    number_of_dustbins = models.PositiveIntegerField()  # count of bins
    size_of_litres = models.FloatField()                # bin size in litres

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.waste_type} - {self.number_of_dustbins} bins ({self.size_of_litres}L)"
    
    
class AuthToken(models.Model):
    token_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        default=secrets.token_hex
    )
    user = models.ForeignKey(
        'User',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='auth_tokens'
    )
    client = models.ForeignKey(
        'Client',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='auth_tokens'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.token[:8]}..."
    


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("sick", "Sick"),
        ("accident", "Accident"),
        ("off", "Off"),   
    ]

    attendance_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    comment = models.TextField(blank=True, null=True)
    absent_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user.name} - {self.date} - {self.status}"

class RoleSalaryPolicy(models.Model):
    role = models.CharField(max_length=50, unique=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    deduction_per_absent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deduction_per_sick_day = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.role} Policy"


import uuid
from datetime import date
from django.db import models

class Salary(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Unpaid", "Unpaid"),
    ]

    salary_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="salaries")
    policy = models.ForeignKey("RoleSalaryPolicy", on_delete=models.CASCADE, related_name="salaries")

    # Salary details
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")

    # Salary period
    month = models.IntegerField(default=date.today().month)
    year = models.IntegerField(default=date.today().year)

    def save(self, *args, **kwargs):
        # Exclude Admin users
        if self.user.role == "Admin":
            raise ValueError("Admin does not have a salary policy.")

        # Link correct policy
        if not self.policy or self.policy.role != self.user.role:
            self.policy = RoleSalaryPolicy.objects.get(role=self.user.role)

        # Auto set base_salary
        if not self.base_salary or self.base_salary == 0:
            self.base_salary = self.policy.base_salary

        # Calculate total salary
        self.total_salary = (self.base_salary + self.bonuses) - self.deductions
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.name} ({self.user.role}) - {self.total_salary}"



from django.db import models
import uuid
from django.utils.timezone import now

class PaidHotelInfo(models.Model):
    STATUS_CHOICES = [
        ("Paid", "Paid"),
        ("Unpaid", "Unpaid"),
    ]

    paid_hotel_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, related_name='paid_info')
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact_phone = models.CharField(max_length=20)
    hadhi = models.CharField(max_length=50)
    currency = models.CharField(max_length=10)
    payment_account = models.CharField(max_length=100)

    # New: track month of payment
    month = models.DateField()  # we’ll store "YYYY-MM-01" (first day of month)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Unpaid")
    paid_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("hotel", "month")  # prevent duplicate records

    def __str__(self):
        return f"{self.name} - {self.month.strftime('%B %Y')} - {self.status}"


# models.py
import uuid
from django.db import models

class PaymentSlip(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('current', 'Current Month'),
        ('previous', 'Previous Month'),
    ]

    slip_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='payment_slips')
    file = models.FileField(upload_to='payment_slips/')  # uploaded by client
    comment = models.TextField(blank=True, null=True)  # client's message
    month_paid = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
    receipt = models.FileField(upload_to='payment_receipts/', blank=True, null=True)  # uploaded by admin
    admin_comment = models.TextField(blank=True, null=True)  # admin feedback to client
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment Slip {self.slip_id} - {self.client.name}"



import uuid
from django.db import models
from django.db.models import Sum
from django.utils.timezone import now
from django.db.models import Sum, F

# Assuming Client model already exists
# and PaymentSlip & CompletedWasteRecord models are defined as you provided

class MonthlyHotelSummary(models.Model):
    """
    Stores aggregated info per hotel per month:
    - Total waste collected (in litres)
    - Total money paid
    """
    summary_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='monthly_summaries')
    month = models.DateField()  # represents the first day of the month (e.g., 2025-10-01)
    
    total_waste_litres = models.FloatField(default=0.0)
    total_amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    # optional: timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('client', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"{self.client.name} - {self.month.strftime('%B %Y')}"

    @classmethod
    def generate_for_month(cls, month_date):
        """
        Aggregate data for all hotels for a given month and save/update MonthlyHotelSummary.
        """
        from .models import CompletedWasteRecord, PaymentSlip, Hotel

        # Aggregate waste per client via schedule → hotel → client
        waste_agg = (
            CompletedWasteRecord.objects
            .filter(
                created_at__year=month_date.year,
                created_at__month=month_date.month
            )
            .values('schedule__hotel__client')
            .annotate(total_litres=Sum(F('number_of_dustbins') * F('size_of_litres')))
        )

        # Aggregate payments per client
        payments_agg = (
            PaymentSlip.objects
            .filter(
                month_paid__year=month_date.year,
                month_paid__month=month_date.month
            )
            .values('client')
            .annotate(total_paid=Sum('amount'))
        )

        # Ensure every hotel client has a summary
        hotels = Hotel.objects.filter(client__isnull=False)
        for hotel in hotels:
            cls.objects.get_or_create(
                client=hotel.client,
                month=month_date.replace(day=1),
                defaults={
                    'total_waste_litres': 0.0,
                    'total_amount_paid': 0.0
                }
            )

        # Merge waste and payments into MonthlyHotelSummary
        for waste in waste_agg:
            client_id = waste['schedule__hotel__client']
            total_waste = waste['total_litres'] or 0.0

            payment = next((p for p in payments_agg if p['client'] == client_id), None)
            total_paid = payment['total_paid'] if payment else 0.0

            cls.objects.update_or_create(
                client_id=client_id,
                month=month_date.replace(day=1),
                defaults={
                    'total_waste_litres': total_waste,
                    'total_amount_paid': total_paid
                }
            )

        return cls.objects.filter(month=month_date.replace(day=1))


# egaz_app/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

class FailedLoginAttempt(models.Model):
    # Either user or client, one will be null
    user = models.OneToOneField('User', null=True, blank=True, on_delete=models.CASCADE)
    client = models.OneToOneField('Client', null=True, blank=True, on_delete=models.CASCADE)
    
    failed_attempts = models.PositiveIntegerField(default=0)
    last_failed_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)

    def record_failure(self):
        self.failed_attempts += 1
        self.last_failed_at = timezone.now()

        # Lock after 3 failed attempts
        if self.failed_attempts >= 3:
            self.is_locked = True
            self.locked_until = timezone.now() + timedelta(minutes=10)
            self.failed_attempts = 0  # reset attempts after lock

        self.save()

    def reset_attempts(self):
        self.failed_attempts = 0
        self.is_locked = False
        self.locked_until = None
        self.last_failed_at = None
        self.save()

    def can_login(self):
        if self.is_locked:
            if self.locked_until and timezone.now() >= self.locked_until:
                self.reset_attempts()
                return True
            return False
        return True
