from rest_framework import serializers
from .models import *
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password


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
        fields = '__all__'

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

class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'

class ScheduleSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    hotel = serializers.PrimaryKeyRelatedField(queryset=Hotel.objects.all(), write_only=True)

    class Meta:
        model = Schedule
        fields = [
            'schedule_id',
            'day',
            'start_time',
            'end_time',
            'status',
            'hotel',        # lazima ipitishwe kwa create/update
            'hotel_name',   # ya kusoma tu
        ]

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

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