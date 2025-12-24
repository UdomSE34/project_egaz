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
    total_rooms = models.IntegerField(default=0, blank=True, null=True)
    type = models.CharField(max_length=50, default="hotel")
    waste_per_day = models.IntegerField( blank=True, null=True)
    currency = models.CharField(max_length=10, default="TZS", blank=True, null=True)
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
    hadhi = models.CharField(max_length=50, blank=True, null=True)
    total_rooms = models.IntegerField(default=0, blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    waste_per_day = models.IntegerField(default=0)
    collection_frequency = models.CharField(max_length=50, default="daily")
    currency = models.CharField(max_length=10, default="TZS")
    payment_account = models.CharField(max_length=100, default="N/A", blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password, check_password
from secrets import token_urlsafe


# Custom User Manager
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email ni lazima")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password or "123456")
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'Admin')
        return self.create_user(email, password, **extra_fields)


# Custom User model
class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20)
    password_hash = models.TextField()

    # Extra details
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=50, null=True, blank=True)

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

    # Roles
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('HR', 'HR'),
        ('Supervisors', 'Supervisors'),
        ('Drivers', 'Drivers'),
        ('Staff', 'Staff'),
        ('Workers', 'Workers'),
        ('Council', 'Council'),
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
    is_staff = models.BooleanField(default=False)  # for admin
    receive_email_notifications = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def save(self, *args, **kwargs):
        if not self.password_hash or not self.password_hash.startswith('pbkdf2_'):
            self.password_hash = make_password(self.password_hash or "123456")
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

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

# models.py
from django.db import models
import uuid
from django.utils import timezone
from datetime import datetime, timedelta

class Schedule(models.Model):
    STATUS_CHOICES = [
        ('Pending','Pending'),
        ('In_Progress','In Progress'),
        ('Completed','Completed'),
    ]

    SLOT_CHOICES = [
        ("06:00 – 12:00", "Morning (06:00 – 12:00)"),
        ("06:00 – 18:00", "Afternoon (06:00 – 18:00)"),
    ]

    DAYS_OF_WEEK = [
        ('Monday','Monday'), ('Tuesday','Tuesday'), ('Wednesday','Wednesday'),
        ('Thursday','Thursday'), ('Friday','Friday'), ('Saturday','Saturday'), ('Sunday','Sunday')
    ]

    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    day = models.CharField(max_length=50, choices=DAYS_OF_WEEK)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    is_visible = models.BooleanField(default=False)
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES, default="Morning")
    hotel = models.ForeignKey("Hotel", on_delete=models.CASCADE, related_name="schedules")
    completion_notes = models.TextField(blank=True, null=True)
    week_start_date = models.DateField(null=True, blank=True)
    schedule_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['week_start_date', 'day', 'slot']
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
        unique_together = ['hotel', 'day', 'slot', 'week_start_date']

    def __str__(self):
        return f"{self.hotel.name} - {self.day} ({self.slot}) - {self.status}"
    
    def save(self, *args, **kwargs):
        """Kokotoa schedule_date kiotomatiki"""
        if self.week_start_date and self.day:
            day_index = {
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
                'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
            }
            days_to_add = day_index.get(self.day, 0)
            self.schedule_date = self.week_start_date + timedelta(days=days_to_add)
        
        # Check if this is new schedule for current week
        is_new = self._state.adding
        
        super().save(*args, **kwargs)
        
        # AUTO-GENERATE: If new schedule for current week, generate upcoming weeks
        if is_new and self.is_current_week():
            from .services.auto_scheduler import AutoScheduler
            AutoScheduler.ensure_upcoming_weeks()
    
    def is_current_week(self):
        """Check if this schedule is for current week"""
        if not self.week_start_date:
            return False
        today = timezone.now().date()
        current_monday = today - timedelta(days=today.weekday())
        return self.week_start_date == current_monday
    
    def is_upcoming_week(self):
        """Check if this schedule is for upcoming week"""
        if not self.week_start_date:
            return False
        today = timezone.now().date()
        current_monday = today - timedelta(days=today.weekday())
        next_monday = current_monday + timedelta(days=7)
        return self.week_start_date == next_monday
    
    def is_future_week(self):
        """Check if this schedule is for future weeks beyond next"""
        if not self.week_start_date:
            return False
        today = timezone.now().date()
        current_monday = today - timedelta(days=today.weekday())
        week_after_next = current_monday + timedelta(days=14)
        return self.week_start_date >= week_after_next
    
    @property
    def week_type(self):
        """Return week type: current, upcoming, future, past"""
        if self.is_current_week():
            return 'current'
        elif self.is_upcoming_week():
            return 'upcoming'
        elif self.is_future_week():
            return 'future'
        else:
            return 'past'
        
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
    
    
    
    
import uuid
import secrets
from django.db import models
from django.core.exceptions import ValidationError

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

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Auth Token'
        verbose_name_plural = 'Auth Tokens'

    def clean(self):
        """Ensure token has exactly one owner: either user OR client."""
        if self.user is None and self.client is None:
            raise ValidationError("Token must be associated with a user or client.")
        if self.user is not None and self.client is not None:
            raise ValidationError("Token cannot be associated with both user and client.")

    def save(self, *args, **kwargs):
        """Save token — permanent, never expires."""
        self.clean()

        # Generate a new token if missing
        if not self.token:
            self.token = secrets.token_hex(32)

        super().save(*args, **kwargs)

    def __str__(self):
        owner = self.user or self.client
        return f"{owner} - {self.token[:8]}..."



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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
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
    
    def get_absolute_url(self):
        """Return full URL to the payment slip file"""
        if self.file:
            return f"https://back.deploy.tz{self.file.url}"
        return ""
    
    def get_receipt_url(self):
        """Return full URL to the receipt file"""
        if self.receipt:
            return f"https://back.deploy.tz{self.receipt.url}"
        return ""

import uuid
from django.db import models
from django.utils.timezone import now
from django.db.models import Sum

class MonthlySummary(models.Model):
    """
    Stores aggregated info for all hotels per month:
    - Total actual waste (from CompletedWasteRecord)
    - Total processed waste (manually updated)
    - Total actual payment (from PaymentSlip)
    - Total processed payment (manually updated)
    - Reports for processed waste & payment (PDF files)
    """

    summary_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    month = models.DateField(unique=True)  # first day of month (YYYY-MM-01)

    # 🔥 CHANGED ALL TO FLOATFIELD - NO MORE DECIMALFIELD
    total_actual_waste = models.FloatField(default=0.0)
    total_processed_waste = models.FloatField(default=0.0)
    total_actual_payment = models.FloatField(default=0.0)  # 🔥 CHANGED
    total_processed_payment = models.FloatField(default=0.0)  # 🔥 CHANGED

    # Fields for storing report files
    processed_waste_report = models.FileField(
        upload_to="monthly_reports/waste/",
        null=True, blank=True
    )
    processed_payment_report = models.FileField(
        upload_to="monthly_reports/payment/",
        null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month']
        verbose_name = "Monthly Summary"
        verbose_name_plural = "Monthly Summaries"

    def __str__(self):
        return f"Overall Summary - {self.month.strftime('%B %Y')}"

    # URL methods
    def get_waste_report_url(self):
        if self.processed_waste_report:
            return f"https://back.deploy.tz{self.processed_waste_report.url}"
        return ""

    def get_payment_report_url(self):
        if self.processed_payment_report:
            return f"https://back.deploy.tz{self.processed_payment_report.url}"
        return ""

    def get_file_url(self, field_name):
        file_field = getattr(self, field_name, None)
        if file_field:
            return f"https://back.deploy.tz{file_field.url}"
        return ""

    @classmethod
    def generate_for_month(cls, month_date):
        """
        Aggregate totals from CompletedWasteRecord and PaymentSlip
        for a given month. Preserves manually updated processed totals.
        """
        from .models import CompletedWasteRecord, PaymentSlip

        # Aggregate actual waste
        actual_waste = (
            CompletedWasteRecord.objects
            .filter(created_at__year=month_date.year, created_at__month=month_date.month)
            .aggregate(total=Sum('size_of_litres'))['total'] or 0.0
        )

        # Aggregate actual payments - SIMPLIFIED
        total_payment = (
            PaymentSlip.objects
            .filter(month_paid__year=month_date.year, month_paid__month=month_date.month)
            .aggregate(total=Sum('amount'))['total']
        )
        actual_payment = float(total_payment or 0.0)  # 🔥 CHANGED TO FLOAT

        # Fetch existing summary or create new one
        summary, created = cls.objects.get_or_create(
            month=month_date.replace(day=1)
        )

        # Update actual totals
        summary.total_actual_waste = actual_waste
        summary.total_actual_payment = actual_payment  # 🔥 NOW FLOAT

        # Only set processed totals if newly created
        if created:
            summary.total_processed_waste = 0.0
            summary.total_processed_payment = 0.0  # 🔥 NOW FLOAT

        summary.save()
        return summary    


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


from django.db import models
import uuid
from datetime import datetime, date

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('not_sent', 'Not Sent'),
        ('sent', 'Sent'),
        ('processing', 'Processing'),
        ('received', 'Received'),
        ('approved', 'Approved'),
    ]

    invoice_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 🔥 REMOVED: invoice_number, amount fields
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, related_name='invoices')
    client = models.ForeignKey('Client', null=True, blank=True, on_delete=models.CASCADE, related_name='invoices')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_sent')
    comment = models.TextField(blank=True, null=True)

    # 🔥 SINGLE FIELD FOR MULTIPLE FILES - NO SIZE LIMITS
    files = models.JSONField(
        default=list,
        blank=True,
        help_text="List of file information: [{'name': 'file1.pdf', 'url': '/media/invoices/file1.pdf'}]"
    )

    month = models.IntegerField(default=datetime.now().month)
    year = models.IntegerField(default=datetime.now().year)

    is_recurring = models.BooleanField(default=True)
    # 🔥 REMOVED: is_received field - using status field instead

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('hotel', 'month', 'year')
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice - {self.hotel.name} - {self.get_month_display()} {self.year}"

    def get_month_display(self):
        """Get month name for display"""
        try:
            return datetime(self.year, self.month, 1).strftime('%B')
        except:
            return "Unknown"
    
    def get_service_period_display(self):
        """Get service period for next month"""
        next_month = self.month + 1 if self.month < 12 else 1
        next_year = self.year if self.month < 12 else self.year + 1
        next_month_name = datetime(next_year, next_month, 1).strftime('%B')
        return f"{next_month_name} {next_year}"
    
    def add_file(self, file_instance):
        """Add a file to the files JSON field"""
        file_info = {
            'id': str(uuid.uuid4()),
            'name': file_instance.name,
            'url': file_instance.url,
            'uploaded_at': datetime.now().isoformat()
        }
        
        if not self.files:
            self.files = []
        
        self.files.append(file_info)
        self.save()
    
    def remove_file(self, file_id):
        """Remove a file from the files JSON field"""
        if self.files:
            self.files = [f for f in self.files if f.get('id') != file_id]
            self.save()

    # 🔥 NEW: Helper property to check if invoice is received
    @property
    def is_received(self):
        """Check if invoice status is 'received'"""
        return self.status == 'received'

    # 🔥 NEW: Helper property to check if invoice is sent
    @property
    def is_sent(self):
        """Check if invoice status is 'sent'"""
        return self.status == 'sent'

    # 🔥 NEW: Helper property to check if invoice is approved
    @property
    def is_approved(self):
        """Check if invoice status is 'approved'"""
        return self.status == 'approved'
    

from django.db import models
import uuid
from datetime import datetime
from django.core.exceptions import ValidationError
import os

class Storage(models.Model):
    DOCUMENT_TYPES = [
        ('contract', 'Contract'),
        ('agreement', 'Agreement'),
        ('license', 'License'),
        ('certificate', 'Certificate'),
        ('report', 'Report'),
        ('invoice', 'Invoice'),
        ('receipt', 'Receipt'),
        ('proposal', 'Proposal'),
        ('quotation', 'Quotation'),
        ('policy', 'Policy'),
        ('manual', 'Manual'),
        ('presentation', 'Presentation'),
        ('spreadsheet', 'Spreadsheet'),
        ('other', 'Other'),
    ]

    # Allowed file extensions
    ALLOWED_EXTENSIONS = [
        # Documents
        'pdf', 'doc', 'docx', 'txt', 'rtf',
        # Spreadsheets
        'xls', 'xlsx', 'csv',
        # Presentations
        'ppt', 'pptx',
        # Images (for document scans)
        'jpg', 'jpeg', 'png', 'gif',
        # Archives
        'zip', 'rar'
    ]

    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='other')
    description = models.TextField(blank=True, null=True)
    
    # File field to store the actual document with validation
    file = models.FileField(
        upload_to='storage/documents/%Y/%m/%d/',
        help_text=f"Allowed file types: {', '.join(ALLOWED_EXTENSIONS)}"
    )
    
    # Store file metadata
    file_size = models.BigIntegerField(default=0)  # in bytes
    file_extension = models.CharField(max_length=10, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    file_type_category = models.CharField(max_length=20, blank=True)  # ADD THIS FIELD
    
    # User who uploaded the document
    uploaded_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='documents')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Storage Document'
        verbose_name_plural = 'Storage Documents'
        indexes = [
            models.Index(fields=['document_type', 'created_at']),
            models.Index(fields=['uploaded_by', 'created_at']),
            models.Index(fields=['file_type_category']),  # ADD THIS INDEX
        ]

    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"

    def clean(self):
        """Validate file type before saving"""
        if self.file:
            # Get file extension
            ext = self.get_file_extension(self.file.name)
            if ext.lower() not in self.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f"File type '{ext}' is not allowed. "
                    f"Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
                )
            
            # Validate file size (e.g., 50MB max)
            max_size = 50 * 1024 * 1024  # 50MB
            if self.file.size > max_size:
                raise ValidationError(f"File size must be less than 50MB. Current size: {self.file.size} bytes")

    def save(self, *args, **kwargs):
        # Handle DRFUserWrapper in uploaded_by field
        if hasattr(self.uploaded_by, '_obj'):
            self.uploaded_by = self.uploaded_by._obj
        
        # Auto-set file metadata before saving
        if self.file:
            self.file_size = self.file.size
            self.file_extension = self.get_file_extension(self.file.name)
            self.original_filename = self.file.name
            self.file_type_category = self.get_file_type_category()  # SET THE CATEGORY
            
            # If name is not set, use the original filename without extension
            if not self.name:
                self.name = os.path.splitext(self.original_filename)[0]
        
        # Run full validation
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def get_file_extension(filename):
        """Extract file extension from filename"""
        return filename.split('.')[-1].lower() if '.' in filename else ''

    def get_file_size_display(self):
        """Return human-readable file size"""
        if self.file_size == 0:
            return "0 Bytes"
        
        size_names = ['Bytes', 'KB', 'MB', 'GB']
        i = 0
        size = self.file_size
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
            
        return f"{size:.2f} {size_names[i]}"

    def get_file_icon(self):
        """Return appropriate icon based on file extension"""
        icon_map = {
            'pdf': '📄',
            'doc': '📝',
            'docx': '📝',
            'txt': '📃',
            'rtf': '📃',
            'xls': '📊',
            'xlsx': '📊',
            'csv': '📊',
            'ppt': '📑',
            'pptx': '📑',
            'jpg': '🖼️',
            'jpeg': '🖼️',
            'png': '🖼️',
            'gif': '🖼️',
            'zip': '📦',
            'rar': '📦',
        }
        return icon_map.get(self.file_extension, '📎')

    def get_file_type_category(self):
        """Categorize file by type for better organization"""
        document_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf']
        spreadsheet_extensions = ['xls', 'xlsx', 'csv']
        presentation_extensions = ['ppt', 'pptx']
        image_extensions = ['jpg', 'jpeg', 'png', 'gif']
        archive_extensions = ['zip', 'rar']

        if self.file_extension in document_extensions:
            return 'document'
        elif self.file_extension in spreadsheet_extensions:
            return 'spreadsheet'
        elif self.file_extension in presentation_extensions:
            return 'presentation'
        elif self.file_extension in image_extensions:
            return 'image'
        elif self.file_extension in archive_extensions:
            return 'archive'
        else:
            return 'other'

    @property
    def download_url(self):
        """Generate download URL for the file"""
        return f"/api/storage/{self.document_id}/download/"

    @property
    def preview_url(self):
        """Generate preview URL for the file (for viewable files)"""
        viewable_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'gif']
        if self.file_extension in viewable_extensions:
            return f"/api/storage/{self.document_id}/preview/"
        return None

    def can_preview(self):
        """Check if file can be previewed in browser"""
        viewable_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'gif']
        return self.file_extension in viewable_extensions

    def get_mime_type(self):
        """Get MIME type for the file"""
        mime_map = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'txt': 'text/plain',
            'csv': 'text/csv',
            'zip': 'application/zip',
            'rar': 'application/x-rar-compressed',
        }
        return mime_map.get(self.file_extension, 'application/octet-stream')