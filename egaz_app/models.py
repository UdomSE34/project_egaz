from django.db import models
import uuid
from django.conf import settings
from django.utils.timezone import now  # <-- add this
import secrets
from django.contrib.auth.hashers import  check_password


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

    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Staff', 'Staff'),
        ('Workers', 'Workers'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Workers')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Ensure password is hashed if creating a new user or password is changed
        if not self.password_hash or not self.password_hash.startswith('pbkdf2_'):
            self.password_hash = make_password(self.password_hash or "123456")
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        """Helper method to check password."""
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return f"{self.name} ({self.role})"
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

# Attendance Records
class AttendanceRecord(models.Model):
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift = models.ForeignKey(WorkShift, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('On_Time','On_Time'),('Late','Late'),('Early_Departure','Early_Departure'),('Absent','Absent')])
    notes = models.TextField(blank=True, null=True)

import uuid
import datetime
from django.db import models

class Schedule(models.Model):
    STATUS_CHOICES = [
        ('Pending','Pending'),
        ('In_Progress','In Progress'),
        ('Completed','Completed'),
        ('Delayed','Delayed'),
    ]

    DAYS_OF_WEEK = [
        ('Monday','Monday'), ('Tuesday','Tuesday'), ('Wednesday','Wednesday'),
        ('Thursday','Thursday'), ('Friday','Friday'), ('Saturday','Saturday'), ('Sunday','Sunday')
    ]

    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    day = models.CharField(max_length=50, choices=DAYS_OF_WEEK)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    
    # Time range
    start_time = models.TimeField()
    end_time = models.TimeField()

    hotel = models.ForeignKey("Hotel", on_delete=models.CASCADE, related_name="schedules")
    completion_notes = models.TextField(blank=True, null=True)
    week_start_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['week_start_date', 'day', 'start_time', 'end_time']
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'

    def save(self, *args, **kwargs):
        # Auto-set week_start_date based on created_at date (Monday of that week)
        if not self.week_start_date:
            today = datetime.date.today()
            monday = today - datetime.timedelta(days=today.weekday())
            self.week_start_date = monday
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hotel.name} - {self.day} {self.start_time}-{self.end_time} - {self.status}"


# Notifications
class Notification(models.Model):
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    related_entity_type = models.CharField(max_length=20, choices=[('Request','Request'),('Schedule','Schedule'),('Attendance','Attendance')])
    related_entity_id = models.UUIDField()
    message_type = models.CharField(max_length=50)
    message_content = models.TextField()
    status = models.CharField(max_length=20, choices=[('Unread','Unread'),('Read','Read'),('Acknowledged','Acknowledged')])
    created_time = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField(null=True, blank=True)

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