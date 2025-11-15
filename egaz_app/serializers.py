from rest_framework import serializers
from .models import *
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password_hash': {'required': False, 'allow_blank': True}  # <-- allow blank / optional
        }

    def create(self, validated_data):
        # If no password given, set default "123456"
        if not validated_data.get("password_hash"):
            validated_data["password_hash"] = make_password("123456")
        else:
            validated_data["password_hash"] = make_password(validated_data["password_hash"])
        return super().create(validated_data)


class ClientSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = Client
        fields = ['client_id', 'name', 'phone', 'email', 'address', 'password', 'created_at']
        read_only_fields = ['client_id', 'created_at']

    def validate_phone(self, value):
        if Client.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A client with this phone number already exists.")
        return value

    def validate_email(self, value):
        if Client.objects.filter(email=value).exists():
            raise serializers.ValidationError("A client with this email already exists.")
        return value

    def create(self, validated_data):
        # Hash password before saving
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    
    
class PendingHotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingHotel
        fields = "__all__"  # includes 'client'


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = '__all__'
        read_only_fields = ['client', 'created_at']

class WasteTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteType
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'

class WorkShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShift
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    hotel = serializers.PrimaryKeyRelatedField(queryset=Hotel.objects.all(), write_only=True)

    class Meta:
        model = Schedule
        fields = [
            'schedule_id',
            'day',
            'slot',
            'status',
            'hotel',
            'hotel_name',
            'is_visible',
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.name", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)
    user_status = serializers.CharField(source="user.status", read_only=True)
    class Meta:
        model = Attendance
        fields = [
            'attendance_id',
            'user',
            'date',
            'status',
            'comment',
            'name',
            'role',
            'user_status',
            'absent_count',
        ]
        
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Notification, User, Client

class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField(read_only=True)
    recipient = serializers.SerializerMethodField(read_only=True)

    # Write-only fields
    sender_type = serializers.ChoiceField(write_only=True, choices=['User', 'Client'])
    sender_id = serializers.UUIDField(write_only=True)
    recipient_type = serializers.ChoiceField(write_only=True, choices=['User', 'Client'], required=False)
    recipient_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Notification
        fields = [
            'notification_id',
            'sender', 'recipient',
            'sender_type', 'sender_id',
            'recipient_type', 'recipient_id',
            'message_content',
            'status',
            'created_time'
        ]
        read_only_fields = ['notification_id', 'status', 'created_time']

    def get_sender(self, obj):
        if isinstance(obj.sender, Client):
            return {"id": obj.sender.client_id, "name": obj.sender.name, "type": "Client", "role": obj.sender.role}
        elif isinstance(obj.sender, User):
            return {"id": obj.sender.user_id, "name": obj.sender.name, "type": "User", "role": obj.sender.role}
        return None

    def get_recipient(self, obj):
        if obj.recipient is None:
            return None  # broadcast
        if isinstance(obj.recipient, Client):
            return {"id": obj.recipient.client_id, "name": obj.recipient.name, "type": "Client", "role": obj.recipient.role}
        elif isinstance(obj.recipient, User):
            return {"id": obj.recipient.user_id, "name": obj.recipient.name, "type": "User", "role": obj.recipient.role}
        return None

    def create(self, validated_data):
        sender_type = validated_data.pop('sender_type')
        sender_id = validated_data.pop('sender_id')
        recipient_type = validated_data.pop('recipient_type', None)
        recipient_id = validated_data.pop('recipient_id', None)

        # Resolve sender
        sender_obj = User.objects.get(user_id=sender_id) if sender_type == 'User' else Client.objects.get(client_id=sender_id)

        # Resolve recipient (None = broadcast)
        if recipient_type and recipient_id:
            recipient_obj = User.objects.get(user_id=recipient_id) if recipient_type == 'User' else Client.objects.get(client_id=recipient_id)
            recipient_model = recipient_obj.__class__
            recipient_content_type = ContentType.objects.get_for_model(recipient_model)
            recipient_object_id = recipient_obj.pk
        else:
            recipient_content_type = None
            recipient_object_id = None

        # Business rules
        if isinstance(sender_obj, Client) and recipient_content_type:
            if not isinstance(recipient_obj, User) or recipient_obj.role not in ['Staff', 'Admin']:
                raise serializers.ValidationError("Clients can only message Staff/Admin users.")
        if isinstance(sender_obj, User) and sender_obj.role == 'Staff' and recipient_content_type:
            if not isinstance(recipient_obj, Client):
                raise serializers.ValidationError("Staff can only message Clients.")

        notification = Notification.objects.create(
            sender_content_type=ContentType.objects.get_for_model(sender_obj.__class__),
            sender_object_id=sender_obj.pk,
            recipient_content_type=recipient_content_type,
            recipient_object_id=recipient_object_id,
            message_content=validated_data['message_content']
        )
        return notification


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'


class CompletedWasteRecordSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer(read_only=True)
    schedule_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = CompletedWasteRecord
        fields = [
            'record_id', 'schedule', 'schedule_id',
            'waste_type', 'number_of_dustbins', 'size_of_litres', 'created_at'
        ]

    def validate_schedule_id(self, value):
        # Ensure the schedule exists
        schedule = Schedule.objects.filter(schedule_id=value).first()
        if not schedule:
            raise serializers.ValidationError("Schedule does not exist")
        return value

    def validate_number_of_dustbins(self, value):
        if value <= 0:
            raise serializers.ValidationError("Number of dustbins must be greater than 0")
        return value

    def validate_size_of_litres(self, value):
        if value <= 0:
            raise serializers.ValidationError("Size of litres must be greater than 0")
        return value

    def create(self, validated_data):
        schedule_id = validated_data.pop('schedule_id')
        schedule = get_object_or_404(Schedule, schedule_id=schedule_id)
        return CompletedWasteRecord.objects.create(schedule=schedule, **validated_data)
    

# Attendance 
  
from rest_framework import serializers
from .models import User, Salary, RoleSalaryPolicy


class RoleSalaryPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleSalaryPolicy
        fields = ['id', 'role', 'base_salary', 'deduction_per_absent', 'deduction_per_sick_day','bonuses']


class SalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Salary
        fields = "__all__"
        
        
        
class UserWithSalarySerializer(serializers.ModelSerializer):
    salary = serializers.SerializerMethodField()
    absences = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'user_id',
            'name',
            'role',
            'salary',
            'absences',
            'status',
        ]

    def get_salary(self, obj):
        """
        Get salary for the given month and year. 
        If no salary exists, fallback to role policy.
        """
        month = self.context.get("month", timezone.now().month)
        year = self.context.get("year", timezone.now().year)

        salary = Salary.objects.filter(user=obj, month=month, year=year).first()
        policy = RoleSalaryPolicy.objects.filter(role=obj.role).first()

        if salary:
            return {
                "salary_id": salary.salary_id,
                "base_salary": float(salary.base_salary),
                "bonuses": float(salary.bonuses),
                "deductions": float(salary.deductions),
                "total_salary": float(salary.total_salary),
                "status": salary.status,
                "month": salary.month,
                "year": salary.year,
            }
        elif policy:
            # fallback to policy values if no salary exists
            base_salary = float(policy.base_salary)
            bonuses = float(policy.bonuses)
            return {
                "salary_id": None,
                "base_salary": base_salary,
                "bonuses": bonuses,
                "deductions": 0.0,
                "total_salary": base_salary + bonuses,
                "status": "Unpaid",
                "month": month,
                "year": year,
            }
        return None

    def get_absences(self, obj):
        """
        Count number of absent days for the user in the given month/year
        """
        month = self.context.get("month", timezone.now().month)
        year = self.context.get("year", timezone.now().year)

        return Attendance.objects.filter(
            user=obj,
            status="absent",
            date__month=month,
            date__year=year
        ).count()

    def get_status(self, obj):
        """
        Return a dynamic status based on is_active and the status field
        """
        if not obj.is_active:
            return "Inactive"
        # Combine is_active + status field
        return obj.status.replace("_", " ").capitalize()
class PaidHotelInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaidHotelInfo
        fields = "__all__"
        
        
class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'name', 'email', 'role', 'receive_email_notifications']
        
        
# serializers.py
from rest_framework import serializers
from .models import PaymentSlip

class PaymentSlipSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = PaymentSlip
        fields = "__all__"
        read_only_fields = ['slip_id', 'created_at']

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and hasattr(obj.file, "url"):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    def get_receipt_url(self, obj):
        request = self.context.get("request")
        if obj.receipt and hasattr(obj.receipt, "url"):
            return request.build_absolute_uri(obj.receipt.url) if request else obj.receipt.url
        return None

class MonthlySummarySerializer(serializers.ModelSerializer):
    waste_report_url = serializers.SerializerMethodField()
    payment_report_url = serializers.SerializerMethodField()
    month_display = serializers.SerializerMethodField()

    class Meta:
        model = MonthlySummary
        fields = '__all__'

    def get_waste_report_url(self, obj):
        return obj.get_waste_report_url()

    def get_payment_report_url(self, obj):
        return obj.get_payment_report_url()

    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y') if obj.month else ""
    
    

class InvoiceSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'invoice_id',
            'hotel',
            'hotel_name',
            'client',
            'client_name',
            'month',
            'year',  # hakujumuishwa hapo awali, kuongeza itasaidia frontend
            'amount',
            'status',
            'is_received',
            'comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['hotel_name', 'client_name']
