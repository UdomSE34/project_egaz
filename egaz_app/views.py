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
from .services.salary_pdf_service import generate_salary_pdf





class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer

class PendingHotelViewSet(viewsets.ModelViewSet):
    queryset = PendingHotel.objects.all()
    serializer_class = PendingHotelSerializer
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
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=["patch"], url_path="submit_comment")
    def submit_comment(self, request, pk=None):
        try:
            print(f"🎯 submit_comment: Received request for user ID: {pk}")
            user = self.get_object()  # Ensures permission checks if used

            action = request.data.get("action")
            comment = request.data.get("comment", "").strip()

            print(f"📥 Action: {action}, Comment: '{comment}'")

            if not action:
                print("❌ Missing 'action' in request data")
                return Response(
                    {"error": "Missing 'action' field. Use 'suspend' or 'delete'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate action
            if action not in ["suspend", "delete"]:
                print(f"❌ Invalid action: {action}")
                return Response(
                    {"error": "Action must be 'suspend' or 'delete'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Save comment to correct field and update status
            if action == "suspend":
                user.status = "pending_suspend"
                user.suspend_comment = comment
                user.delete_comment = None  # Clear conflicting comment
                print(f"✅ User {user.user_id} marked for suspension. Comment saved.")

            elif action == "delete":
                user.status = "pending_delete"
                user.delete_comment = comment
                user.suspend_comment = None  # Clear conflicting comment
                print(f"✅ User {user.user_id} marked for deletion. Comment saved.")

            # Save to DB
            user.save()

            # Serialize and return
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Error in submit_comment: {str(e)}")
            return Response(
                {"error": "An internal error occurred.", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='approve-action')
    def approve_action(self, request, pk=None):
        try:
            print(f"🛡️ approve_action: Admin action for user ID: {pk}")
            user = self.get_object()

            action = request.data.get("action")  # approve / reject
            type = request.data.get("type")      # suspend / delete

            print(f"📥 Admin Action: {action}, Type: {type}")

            # Validate current status
            if user.status not in ['pending_suspend', 'pending_delete']:
                print(f"🚫 User {user.user_id} has no pending action. Status: {user.status}")
                return Response(
                    {"error": "User has no pending action to approve or reject."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate inputs
            if action not in ["approve", "reject"]:
                print(f"❌ Invalid admin action: {action}")
                return Response(
                    {"error": "Action must be 'approve' or 'reject'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if type not in ["suspend", "delete"]:
                print(f"❌ Invalid type: {type}")
                return Response(
                    {"error": "Type must be 'suspend' or 'delete'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Approve or reject logic
            if action == "approve":
                if type == "suspend" and user.status == "pending_suspend":
                    user.status = "suspended"
                    print(f"✅ User {user.user_id} suspended.")
                elif type == "delete" and user.status == "pending_delete":
                    user.status = "deleted"
                    print(f"✅ User {user.user_id} marked as deleted.")
                else:
                    print(f"⚠️ Mismatch: type={type} but status={user.status}")
                    return Response(
                        {"error": "Action type does not match pending request."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            elif action == "reject":
                user.status = "active"
                # # Clear the comment of the rejected action
                # if type == "suspend":
                #     user.suspend_comment = None
                # elif type == "delete":
                    # user.delete_comment = None
                print(f"🔁 User {user.user_id} rejected {type} request. Restored to active.")

            # Save changes
            user.save()
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Error in approve_action: {str(e)}")
            return Response(
                {"error": "An internal error occurred during approval.", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
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


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer

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

    def get_queryset(self):
        return User.objects.filter(is_active=True).exclude(role="Admin")

    def list(self, request, *args, **kwargs):
        month = int(request.query_params.get("month", timezone.now().month))
        year = int(request.query_params.get("year", timezone.now().year))
        users = self.get_queryset()
        result = []

        for user in users:
            # Use util to auto-create or get existing salary
            salary = calculate_user_salary(user, month, year, auto_create=True)

            if salary:
                salary_data = {
                    "salary_id": salary.salary_id,
                    "base_salary": float(salary.base_salary),
                    "bonuses": float(salary.bonuses),
                    "deductions": float(salary.deductions),
                    "total_salary": float(salary.total_salary),
                    "status": salary.status,
                    "month": salary.month,
                    "year": salary.year,
                }
                base_salary = float(salary.base_salary)
                bonuses = float(salary.bonuses)
            else:
                # fallback if no salary created (e.g., Admin or no policy)
                policy = RoleSalaryPolicy.objects.filter(role=user.role).first()
                base_salary = policy.base_salary if policy else 0
                bonuses = policy.bonuses if policy else 0
                salary_data = {
                    "salary_id": None,
                    "base_salary": base_salary,
                    "bonuses": bonuses,
                    "deductions": 0,
                    "total_salary": base_salary + bonuses,
                    "status": "N/A",
                    "month": month,
                    "year": year,
                }

            result.append({
                "user_id": user.user_id,
                "name": user.name,
                "role": user.role,
                "base_salary": base_salary,
                "bonuses": bonuses,
                "salary": salary_data,
            })

        return Response(result)

    @action(detail=False, methods=["post"])
    def calculate_salaries(self, request):
        month = int(request.data.get("month", timezone.now().month))
        year = int(request.data.get("year", timezone.now().year))

        # Auto-generate salaries for all non-admin users using util
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
    lookup_field = "role"
    
class SalaryViewSet(viewsets.ModelViewSet):
    queryset = Salary.objects.all()
    serializer_class = SalarySerializer
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
from .models import Attendance, User
from .serializers import AttendanceSerializer
from .salary.utils import calculate_user_salary
from .attendance.utils import ensure_attendance_for_month

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
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

    def perform_create(self, serializer):
        attendance, created = Attendance.objects.update_or_create(
            user=serializer.validated_data["user"],
            date=serializer.validated_data["date"],
            defaults=serializer.validated_data
        )
        # auto update salary
        calculate_user_salary(attendance.user, attendance.date.month, attendance.date.year, auto_create=True)

    def perform_update(self, serializer):
        attendance = serializer.save()
        calculate_user_salary(attendance.user, attendance.date.month, attendance.date.year, auto_create=True)

    def perform_destroy(self, instance):
        month = instance.date.month
        year = instance.date.year
        user = instance.user
        instance.delete()
        calculate_user_salary(user, month, year, auto_create=True)
        
        
        
        
        
# Admin Hotel Paid info
from .utils import mark_hotel_as_paid, mark_hotel_as_unpaid

class PaidHotelInfoViewSet(viewsets.ModelViewSet):
    queryset = PaidHotelInfo.objects.all()
    serializer_class = PaidHotelInfoSerializer

    @action(detail=True, methods=["patch"])
    def mark_paid(self, request, pk=None):
        hotel_info = mark_hotel_as_paid(pk)
        if not hotel_info:
            return Response({"error": "Hotel not found"}, status=404)
        serializer = self.get_serializer(hotel_info)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def mark_unpaid(self, request, pk=None):
        hotel_info = mark_hotel_as_unpaid(pk)
        if not hotel_info:
            return Response({"error": "Hotel not found"}, status=404)
        serializer = self.get_serializer(hotel_info)
        return Response(serializer.data)
