from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from .models import *
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from .serializers import *
from django.http import HttpResponse
from django.utils.timezone import now
from datetime import date, timedelta
from .models import Schedule
from .services.pdf_service import PdfService  # 👈 import your PdfService


class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer

class PendingHotelViewSet(viewsets.ModelViewSet):
    queryset = PendingHotel.objects.all()
    serializer_class = PendingHotelSerializer
    
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        pending = self.get_object()
        # create real hotel
        hotel = Hotel.objects.create(
            name=pending.name,
            address=pending.address,
            email=pending.email,
            contact_phone=pending.contact_phone,
            hadhi=pending.hadhi,
            total_rooms=pending.total_rooms,
            type=pending.type,
            waste_per_day=pending.waste_per_day,
            collection_frequency=pending.collection_frequency,
            currency=pending.currency,
            payment_account=pending.payment_account,
        )
        pending.status = "approved"
        pending.save()
        return Response({"message": "Hotel approved and added to hotels."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        pending = self.get_object()
        pending.status = "rejected"
        pending.save()
        return Response({"message": "Hotel rejected."}, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    # Custom registration action
    @action(detail=False, methods=['post'], url_path='register')
    def register_client(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save(role='client')  # ensure role is 'client'
            return Response(
                {
                    'message': 'Client registered successfully',
                    'client_id': client.client_id
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WasteTypeViewSet(viewsets.ModelViewSet):
    queryset = WasteType.objects.all()
    serializer_class = WasteTypeSerializer

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class WorkShiftViewSet(viewsets.ModelViewSet):
    queryset = WorkShift.objects.all()
    serializer_class = WorkShiftSerializer

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer

class CompletedWasteRecordViewSet(viewsets.ModelViewSet):
    queryset = CompletedWasteRecord.objects.all()
    serializer_class = CompletedWasteRecordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # ✅ ensures JSON error response
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

def download_schedules_pdf(request):
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Get all schedules where week_start_date is this week or last week
    # This ensures we only check relevant schedules instead of all
    relevant_weeks = [yesterday - timedelta(days=yesterday.weekday()),  # Monday of last week
                      today - timedelta(days=today.weekday())]          # Monday of this week

    schedules = Schedule.objects.filter(week_start_date__in=relevant_weeks).select_related('hotel')

    # Pass schedules to PDF service
    pdf_bytes = PdfService.generate_pdf(schedules)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="today_yesterday_schedules.pdf"'
    return response


@api_view(['POST'])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"detail": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    # 1️⃣ Try User login (Admin/Staff/Workers)
    try:
        user = User.objects.get(email=email)
        if check_password(password, user.password_hash):
            # Ensure only user is set for token
            token_obj, created = AuthToken.objects.get_or_create(user=user, client=None)
            return Response({
                "token": token_obj.token,
                "user": {
                    "id": str(user.user_id),
                    "name": user.name,
                    "email": user.email,
                    "role": user.role
                }
            })
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        pass

    # 2️⃣ Try Client login
    try:
        client = Client.objects.get(email=email)
        if check_password(password, client.password):
            # Ensure only client is set for token
            token_obj, created = AuthToken.objects.get_or_create(user=None, client=client)
            return Response({
                "token": token_obj.token,
                "user": {
                    "id": str(client.client_id),
                    "name": client.name,
                    "email": client.email,
                    "role": "client"
                }
            })
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    except Client.DoesNotExist:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)