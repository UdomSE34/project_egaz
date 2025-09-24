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
from datetime import date, timedelta
from .models import Schedule
from .services.pdf_service import PdfService  # 👈 import your PdfService
from .services.salary_pdf_service import generate_salary_pdf
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny
from .authentication import CustomTokenAuthentication






class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

class PendingHotelViewSet(viewsets.ModelViewSet):
    queryset = PendingHotel.objects.all()
    serializer_class = PendingHotelSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access
    # Hakuna authentication/permissions

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        pending = self.get_object()
        Hotel.objects.create(
            client=pending.client,
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
        return Response({"message": "Hotel approved and added to hotels."}, status=200)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        pending = self.get_object()
        pending.status = "rejected"
        pending.save()
        return Response({"message": "Hotel rejected."}, status=200)
    
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    Supports standard CRUD + custom actions for suspend/delete/activate workflows.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

    @action(detail=True, methods=["patch"], url_path="submit_comment")
    def submit_comment(self, request, pk=None):
        """
        Submit a comment for suspension or deletion (sets pending status).
        Used by requester to explain why they want suspend/delete.
        """
        try:
            user = self.get_object()
            action = request.data.get("action")
            comment = request.data.get("comment", "").strip()

            if not action:
                return Response(
                    {"error": "Missing 'action' field. Use 'suspend' or 'delete'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if action not in ["suspend", "delete"]:
                return Response(
                    {"error": "Action must be 'suspend' or 'delete'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not comment:
                return Response({"error": "A reason/comment is required."}, status=400)

            if action == "suspend":
                user.status = "pending_suspend"
                user.suspend_comment = comment
                user.delete_comment = None

            elif action == "delete":
                user.status = "pending_delete"
                user.delete_comment = comment
                user.suspend_comment = None

            user.save()
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "An internal error occurred.", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'], url_path='approve-action')
    def approve_action(self, request, pk=None):
        """
        Unified endpoint to approve/reject suspend, activate, or delete actions.
        Enforces a comment for every action.
        Works immediately, regardless of pending status.
        """
        try:
            user = self.get_object()
            action = request.data.get("action")  # approve / reject
            type_val = request.data.get("type")  # suspend / delete / activate
            comment = request.data.get("comment", "").strip()

            if action not in ["approve", "reject"]:
                return Response(
                    {"error": "Action must be 'approve' or 'reject'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if type_val not in ["suspend", "delete", "activate"]:
                return Response(
                    {"error": "Type must be 'suspend', 'delete', or 'activate'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not comment:
                return Response({"error": "A reason/comment is required for this action."}, status=400)

            # Process APPROVE
            if action == "approve":
                if type_val == "suspend":
                    user.status = "suspended"
                    user.finaldelete_comment = comment

                elif type_val == "delete":
                    user.status = "deleted"
                    user.finaldelete_comment = comment
                    user.deleted_at = timezone.now()

                elif type_val == "activate":
                    user.status = "active"
                    user.finaldelete_comment = comment  # optional to store reason

            # Process REJECT
            elif action == "reject":
                user.status = "active"
                if type_val == "suspend":
                    user.finaldelete_comment = comment
                elif type_val == "delete":
                    user.finaldelete_comment = comment
                elif type_val == "activate":
                    user.finaldelete_comment = comment  # optional

            user.save()
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "An internal error occurred during approval.", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

                      
            
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access
    
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
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

class WorkShiftViewSet(viewsets.ModelViewSet):
    queryset = WorkShift.objects.all()
    serializer_class = WorkShiftSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access
    lookup_field = "schedule_id"

    @action(detail=False, methods=["patch"])
    def update_visibility_by_hotel(self, request):
        hotel_name = request.data.get("hotel_name")
        is_visible = request.data.get("is_visible", True)

        if not hotel_name:
            return Response({"error": "hotel_name required"}, status=400)

        updated = Schedule.objects.filter(hotel__name=hotel_name).update(is_visible=is_visible)
        return Response({"updated": updated, "hotel_name": hotel_name, "is_visible": is_visible})
    
from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.db import models
from .models import Notification, User, Client
from .serializers import NotificationSerializer
import uuid


class NotificationViewSet(viewsets.ModelViewSet):
    """
    Handles direct messages (User ⇄ Client) and client broadcasts (Client → all Staff/Admin)
    """
    serializer_class = NotificationSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access
    queryset = Notification.objects.all().order_by('-created_time')

    def get_queryset(self):
        """
        Fetch notifications for inbox or outbox.
        Broadcast messages (recipient=None) appear in inbox.
        """
        recipient_type = self.request.query_params.get("recipient_type")
        recipient_id_str = self.request.query_params.get("recipient_id")
        sender_type = self.request.query_params.get("sender_type")
        sender_id_str = self.request.query_params.get("sender_id")

        # Inbox
        if recipient_type and recipient_id_str:
            try:
                recipient_id = uuid.UUID(recipient_id_str)
            except ValueError:
                return Notification.objects.none()

            try:
                recipient = User.objects.get(user_id=recipient_id) if recipient_type == "User" else Client.objects.get(client_id=recipient_id)
            except (User.DoesNotExist, Client.DoesNotExist):
                return Notification.objects.none()

            content_type = ContentType.objects.get_for_model(recipient.__class__)
            return Notification.objects.filter(
                models.Q(recipient_content_type=content_type, recipient_object_id=recipient.pk) |
                models.Q(recipient_content_type__isnull=True)  # broadcast messages
            ).order_by('-created_time')

        # Outbox
        if sender_type and sender_id_str:
            try:
                sender_id = uuid.UUID(sender_id_str)
            except ValueError:
                return Notification.objects.none()

            try:
                sender = User.objects.get(user_id=sender_id) if sender_type == "User" else Client.objects.get(client_id=sender_id)
            except (User.DoesNotExist, Client.DoesNotExist):
                return Notification.objects.none()

            content_type = ContentType.objects.get_for_model(sender.__class__)
            return Notification.objects.filter(
                sender_content_type=content_type,
                sender_object_id=sender.pk
            ).order_by('-created_time')

        return Notification.objects.none()

    def perform_create(self, serializer):
        """
        Create direct messages or broadcast messages.
        """
        data = self.request.data
        sender_type = data.get("sender_type")
        sender_id = data.get("sender_id")
        recipient_type = data.get("recipient_type")
        recipient_id = data.get("recipient_id")
        message_content = data.get("message_content")

        if not sender_type or not sender_id or not message_content:
            raise serializers.ValidationError("sender_type, sender_id, and message_content are required.")

        # Normalize recipient_id for broadcast
        if recipient_id in (None, "", "null"):
            recipient_id = None
            recipient_type = None

        # Resolve sender
        try:
            sender = User.objects.get(user_id=sender_id) if sender_type == "User" else Client.objects.get(client_id=sender_id)
        except (User.DoesNotExist, Client.DoesNotExist):
            raise serializers.ValidationError({"sender_id": "Invalid sender ID"})

        # Broadcast message
        if recipient_id is None:
            if not isinstance(sender, Client):
                raise serializers.ValidationError("Only Clients can send broadcast messages")
            serializer.save(
                sender_content_type=ContentType.objects.get_for_model(sender.__class__),
                sender_object_id=sender.pk,
                recipient_content_type=None,
                recipient_object_id=None,
            )
            return

        # Direct message
        if not recipient_type:
            raise serializers.ValidationError({"recipient_type": "recipient_type is required for direct messages"})

        try:
            recipient = User.objects.get(user_id=recipient_id) if recipient_type == "User" else Client.objects.get(client_id=recipient_id)
        except (User.DoesNotExist, Client.DoesNotExist):
            raise serializers.ValidationError({"recipient_id": "Invalid recipient ID"})

        # Business rules
        if isinstance(sender, Client) and not (isinstance(recipient, User) and recipient.role in ["Staff", "Admin"]):
            raise serializers.ValidationError("Clients can only message Staff/Admin")
        if isinstance(sender, User) and sender.role == "Staff" and not isinstance(recipient, Client):
            raise serializers.ValidationError("Staff can only message Clients")

        serializer.save(
            sender_content_type=ContentType.objects.get_for_model(sender.__class__),
            sender_object_id=sender.pk,
            recipient_content_type=ContentType.objects.get_for_model(recipient.__class__),
            recipient_object_id=recipient.pk,
        )

    @action(detail=False, methods=["post"])
    def mark_as_read(self, request):
        """
        Marks a list of notifications as 'Read'
        """
        notification_ids = request.data.get("notification_ids", [])
        if not notification_ids:
            return Response({"error": "No notification IDs provided"}, status=400)

        try:
            uuids = [uuid.UUID(id_str) for id_str in notification_ids]
        except ValueError:
            return Response({"error": "Invalid UUID format"}, status=400)

        updated_count = Notification.objects.filter(notification_id__in=uuids).update(status="Read")
        return Response({"message": f"{updated_count} notification(s) marked as read"}, status=200)


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

class CompletedWasteRecordViewSet(viewsets.ModelViewSet):
    queryset = CompletedWasteRecord.objects.all()
    serializer_class = CompletedWasteRecordSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

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

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"detail": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    # 1️⃣ Try User login (Admin/Staff/Workers)
    try:
        user = User.objects.get(email=email)
        if check_password(password, user.password_hash):
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


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

    def get_queryset(self):
        return Attendance.objects.all()


# Admin Salary Management
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Salary, RoleSalaryPolicy, Attendance
from .serializers import UserWithSalarySerializer
from .salary.utils import calculate_user_salary, update_salary_for_all_users

class UserWithSalaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserWithSalarySerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

    def get_queryset(self):
        """
        Only active non-admin users are fetched.
        """
        return User.objects.filter(is_active=True).exclude(role__iexact="admin")

    def list(self, request, *args, **kwargs):
        """
        List all active users with salary, absences, and dynamic status.
        Month and year are passed via query params; defaults to current month/year.
        """
        month = int(request.query_params.get("month", timezone.now().month))
        year = int(request.query_params.get("year", timezone.now().year))

        users = self.get_queryset()
        serializer = self.get_serializer(
            users,
            many=True,
            context={"month": month, "year": year}  # pass month/year to serializer
        )
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def calculate_salaries(self, request):
        """
        Calculate or update salaries for all active non-admin users for a given month/year.
        """
        month = int(request.data.get("month", timezone.now().month))
        year = int(request.data.get("year", timezone.now().year))

        created_count = update_salary_for_all_users(month, year)

        return Response({
            "message": f"Salaries calculated for {created_count} users",
            "month": month,
            "year": year,
        })

class RoleSalaryPolicyViewSet(viewsets.ModelViewSet):
    """Manage base salaries and deduction rules for each role."""
    queryset = RoleSalaryPolicy.objects.all()
    serializer_class = RoleSalaryPolicySerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access
    lookup_field = "role"
    
class SalaryViewSet(viewsets.ModelViewSet):
    queryset = Salary.objects.all()
    serializer_class = SalarySerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access
    @action(detail=True, methods=["patch"])
    def mark_paid(self, request, pk=None):
        salary = get_object_or_404(Salary, pk=pk)
        salary.status = "Paid"
        salary.save()
        serializer = self.get_serializer(salary)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"])
    def mark_unpaid(self, request, pk=None):
        salary = get_object_or_404(Salary, pk=pk)
        salary.status = "Unpaid"
        salary.save()
        serializer = self.get_serializer(salary)
        return Response(serializer.data, status=status.HTTP_200_OK)

# To export salaries as PDF
    @action(detail=False, methods=["get"])
    def export_pdf(self, request):
        """Export salaries as a styled PDF"""
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = 'attachment; filename="salary_report.pdf"'

        salaries = Salary.objects.select_related("user").all()
        return generate_salary_pdf(salaries, response)
    
from rest_framework import viewsets
from django.utils import timezone
from egaz_app.models import Attendance, User
from egaz_app.serializers import AttendanceSerializer
from egaz_app.salary.utils import calculate_user_salary
from egaz_app.attendance.utils import ensure_attendance_for_month


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access
    lookup_field = "attendance_id"

    def get_queryset(self):
        user_id = self.request.query_params.get("user")
        month = int(self.request.query_params.get("month", timezone.now().month))
        year = int(self.request.query_params.get("year", timezone.now().year))

        users = User.objects.exclude(role="Admin")
        if user_id:
            users = users.filter(user_id=user_id)

        # Auto-create attendance for each user using utils
        for user in users:
            ensure_attendance_for_month(user, month, year)

        qs = Attendance.objects.filter(date__month=month, date__year=year)
        if user_id:
            qs = qs.filter(user__user_id=user_id)
        return qs

    def update_absent_count(self, attendance):
        """Calculate total absences for the month and update the field."""
        month = attendance.date.month
        year = attendance.date.year
        user = attendance.user

        total_absent = Attendance.objects.filter(
            user=user, date__month=month, date__year=year, status="absent"
        ).count()

        attendance.absent_count = total_absent
        attendance.save()

    def perform_create(self, serializer):
        attendance, created = Attendance.objects.update_or_create(
            user=serializer.validated_data["user"],
            date=serializer.validated_data["date"],
            defaults=serializer.validated_data
        )

        # ✅ Update absent_count based on month
        self.update_absent_count(attendance)

        # ✅ Auto update salary
        calculate_user_salary(attendance.user, attendance.date.month, attendance.date.year, auto_create=True)

    def perform_update(self, serializer):
        attendance = serializer.save()

        # ✅ Update absent_count based on month
        self.update_absent_count(attendance)

        # ✅ Auto update salary
        calculate_user_salary(attendance.user, attendance.date.month, attendance.date.year, auto_create=True)

    def perform_destroy(self, instance):
        month = instance.date.month
        year = instance.date.year
        user = instance.user
        instance.delete()

        # Update absent count for remaining records of that month
        remaining_attendances = Attendance.objects.filter(user=user, date__month=month, date__year=year)
        for att in remaining_attendances:
            self.update_absent_count(att)

        calculate_user_salary(user, month, year, auto_create=True)

        
        
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PaidHotelInfo
from .serializers import PaidHotelInfoSerializer
from .utils import mark_hotel_as_paid, mark_hotel_as_unpaid


class PaidHotelInfoViewSet(viewsets.ModelViewSet):
    queryset = PaidHotelInfo.objects.all()
    serializer_class = PaidHotelInfoSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

    @action(detail=True, methods=["patch"])
    def mark_paid(self, request, pk=None):
        hotel_info = mark_hotel_as_paid(pk)
        if not hotel_info:
            return Response({"error": "Hotel not found"}, status=404)

        serializer = self.get_serializer(hotel_info)
        return Response({
            "message": "Hotel marked as paid and email sent.",
            "data": serializer.data
        })

    @action(detail=True, methods=["patch"])
    def mark_unpaid(self, request, pk=None):
        hotel_info = mark_hotel_as_unpaid(pk)
        if not hotel_info:
            return Response({"error": "Hotel not found"}, status=404)

        serializer = self.get_serializer(hotel_info)
        return Response({
            "message": "Hotel marked as unpaid.",
            "data": serializer.data
        })



class UserNotificationViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserNotificationSerializer
    authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
    permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

    # Optional: endpoint to toggle email notification
    @action(detail=True, methods=['patch'])
    def toggle_email(self, request, pk=None):
        user = self.get_object()
        user.receive_email_notifications = request.data.get('receive_email_notifications', False)
        user.save()
        return Response({'success': True, 'receive_email_notifications': user.receive_email_notifications})
    


from rest_framework import viewsets, permissions
from .models import PaymentSlip
from .serializers import PaymentSlipSerializer
from .authentication import CustomTokenAuthentication  # your custom auth
from rest_framework.parsers import MultiPartParser, FormParser

class PaymentSlipViewSet(viewsets.ModelViewSet):
    queryset = PaymentSlip.objects.all().select_related('client')
    serializer_class = PaymentSlipSerializer
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # allow file upload

    def perform_create(self, serializer):
        # Automatically attach the logged-in client if needed
        if hasattr(self.request.user, 'client'):  # assuming user has client attribute
            serializer.save(client=self.request.user.client)
        else:
            serializer.save()


# views.py
from django.http import HttpResponse, Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import PaymentSlip
import mimetypes

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_payment_slip(request, slip_id):
    try:
        slip = PaymentSlip.objects.get(slip_id=slip_id)
        if slip.client.id != request.user.id:
            return Http404("Not allowed")
        
        file_handle = slip.file.open("rb")
        mime_type, _ = mimetypes.guess_type(slip.file.name)
        response = HttpResponse(file_handle, content_type=mime_type)
        response["Content-Disposition"] = "inline; filename=" + slip.file.name
        return response
    except PaymentSlip.DoesNotExist:
        raise Http404("Slip not found")
