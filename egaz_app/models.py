from django.db import models
import uuid
from django.utils.timezone import now  # <-- add this


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
# Users
class User(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password_hash = models.TextField()
    role = models.CharField(max_length=20, choices=[
        ('Hotel_Manager','Hotel_Manager'), ('Admin','Admin'),
        ('Scheduler','Scheduler'), ('Driver','Driver'),
        ('Collector','Collector')
    ])
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True)
    team_id = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    # request = models.ForeignKey('ServiceRequest', on_delete=models.CASCADE)
    day = models.CharField(max_length=50, choices=DAYS_OF_WEEK)  # Increased from 20 to 50
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')  # Increased from 20 to 50
    time = models.TimeField()
    hotel = models.ForeignKey("Hotel", on_delete=models.CASCADE, related_name="schedules")
    completion_notes = models.TextField(blank=True, null=True)
    week_start_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['week_start_date', 'day', 'time']
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'

    def __str__(self):
        # DO NOT use self.request here
        return f"{self.hotel.name} - {self.day} {self.time} - {self.status}"

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
