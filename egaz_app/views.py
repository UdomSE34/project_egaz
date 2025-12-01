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
from .services.pdf_service import PdfService  # 👈 import your PdfService
from .services.salary_pdf_service import generate_salary_pdf
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny
from .authentication import CustomTokenAuthentication
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from django.db import transaction


class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        TEMPORARY: Return all hotels for testing
        """
        print("🔍 TEMPORARY: Returning ALL hotels")
        return Hotel.objects.all()

    @action(detail=False, methods=['get'])
    def unclaimed_hotels(self, request):
        try:
            search = request.query_params.get("search", "").strip()

            hotels = Hotel.objects.filter(client__isnull=True)

            if search:
                hotels = hotels.filter(
                    Q(name__icontains=search) |
                    Q(address__icontains=search)
                )

            serializer = self.get_serializer(hotels, many=True)
            return Response(serializer.data)

        except Exception as e:
            print("❌ ERROR:", e)
            return Response(
                {"detail": "Failed to load unclaimed hotels."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['patch'])
    def claim_hotels(self, request):
        """
        Client claims hotels – also update or create invoices for claimed hotels
        """
        try:
            client = request.user
            hotel_ids = request.data.get("hotel_ids", [])

            if not hotel_ids:
                return Response(
                    {"detail": "Chagua hoteli unazodai."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            unclaimed_hotels = Hotel.objects.filter(
                hotel_id__in=hotel_ids,
                client__isnull=True
            )

            claimed_count = unclaimed_hotels.count()

            if claimed_count == 0:
                return Response(
                    {"detail": "Hakuna hoteli zilizopatikana kwa kudaiwa."},
                    status=status.HTTP_404_NOT_FOUND
                )

            updated_invoices_count = 0
            current_month = datetime.now().month
            current_year = datetime.now().year

            with transaction.atomic():
                # 1️⃣ Assign hotels to client
                unclaimed_hotels.update(client=client)

                # 2️⃣ Update existing invoices or create new ones
                for hotel in unclaimed_hotels:
                    invoice = Invoice.objects.filter(
                        hotel=hotel,
                        month=current_month,
                        year=current_year
                    ).first()

                    if invoice:
                        invoice.client = client
                        invoice.save()
                    else:
                        Invoice.objects.create(
                            hotel=hotel,
                            client=client,
                            status='not_sent',
                            month=current_month,
                            year=current_year,
                            files=[]
                        )
                    updated_invoices_count += 1

            return Response({
                "message": f"Umekudai hoteli {claimed_count} kikamilifu!",
                "claimed_count": claimed_count,
                "invoices_updated": updated_invoices_count
            })

        except Exception as e:
            print("❌ ERROR:", e)
            return Response(
                {"detail": "Hitilafu imetokea wakati wa kudai hoteli."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PendingHotel, Hotel
from .serializers import PendingHotelSerializer
from .utils import (
    send_hotel_created_email,
    send_hotel_approved_email,
    send_hotel_rejected_email,
)


from .authentication import CustomTokenAuthentication


class PendingHotelViewSet(viewsets.ModelViewSet):
    queryset = PendingHotel.objects.all()
    serializer_class = PendingHotelSerializer
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        hotel = serializer.save()
        send_hotel_created_email(hotel)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        pending = self.get_object()
        hotel = Hotel.objects.create(
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

        send_hotel_approved_email(hotel)
        return Response({"message": "Hotel approved and email sent."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        pending = self.get_object()
        pending.status = "rejected"
        pending.save()
        send_hotel_rejected_email(pending)
        return Response({"message": "Hotel rejected and email sent."}, status=status.HTTP_200_OK)
    

    
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

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import secrets
import logging

from .models import Client, AuthToken
from .serializers import ClientSerializer
from .services.email_registration import send_registration_email
from .authentication import CustomTokenAuthentication

# Configure a logger
logger = logging.getLogger(__name__)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    authentication_classes = [CustomTokenAuthentication]  # Token auth
    permission_classes = [IsAuthenticated]  # Default

    def get_permissions(self):
        """
        Allow unauthenticated access for registration only.
        """
        if getattr(self, 'action', None) == "register_client":
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='register')
    def register_client(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save(role='client')

            # Create auth token automatically
            token = AuthToken.objects.create(
                client=client,
                token=secrets.token_hex(32)
            )

            # Send registration email safely
            try:
                email_sent = send_registration_email(client)
            except Exception as e:
                email_sent = False
                logger.error(f"Failed to send registration email to {client.email}: {e}")

            # Build response
            response_data = {
                "message": "Client registered successfully",
                "client_id": client.client_id,
                "token": token.token,
                "email_sent": email_sent
            }

            if not email_sent:
                response_data["warning"] = "Registration successful but email notification failed."

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# clients/views_admin.py - For admin/staff management
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import secrets
import logging
from django.contrib.auth.hashers import make_password

from .models import Client, AuthToken
from .serializers import ClientManagementSerializer

logger = logging.getLogger(__name__)

class ClientManagementViewSet(viewsets.ModelViewSet):
    """
    ADMIN/STAFF API - For managing clients (CRUD operations)
    """
    queryset = Client.objects.all().order_by('-created_at')
    serializer_class = ClientManagementSerializer
    authentication_classes = [CustomTokenAuthentication]  # Token auth
    permission_classes = [IsAuthenticated]  # Default

    def get_queryset(self):
        """
        Return all clients for admin/staff
        """
        return Client.objects.all().order_by('-created_at')

    @action(detail=False, methods=['get'], url_path='list-all')
    def list_all_clients(self, request):
        """
        ADMIN: Get all clients with pagination
        """
        try:
            clients = self.get_queryset()
            
            # Debug info
            print(f"📊 Admin fetching {clients.count()} clients")
            
            page = self.paginate_queryset(clients)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(clients, many=True)
            return Response({
                "count": clients.count(),
                "clients": serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error in admin list_all_clients: {e}")
            return Response(
                {"error": "Failed to fetch clients", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request):
        """
        ADMIN: Create new client
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save(role='client')
            
            # Create auth token
            token = AuthToken.objects.create(
                client=client,
                token=secrets.token_hex(32)
            )
            
            response_data = {
                "message": "Client created successfully by admin",
                "client_id": client.client_id,
                "token": token.token
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        ADMIN: Update client information
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            # Handle password hashing if password is being updated
            if 'password' in request.data and request.data['password']:
                if not request.data['password'].startswith('pbkdf2_'):
                    request.data['password'] = make_password(request.data['password'])
            
            self.perform_update(serializer)
            return Response({
                "message": "Client updated successfully by admin", 
                "client": serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        ADMIN: Delete client
        """
        instance = self.get_object()
        client_name = instance.name
        self.perform_destroy(instance)
        
        return Response({
            "message": f"Client '{client_name}' deleted successfully by admin"
        }, status=status.HTTP_200_OK)


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
    permission_classes = [IsAuthenticated] # Only authenticated users/clients can access
   
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from .authentication import CustomTokenAuthentication
from .models import Schedule
from .serializers import ScheduleSerializer
from .utils import send_apology_email
from .services.pdf_service import PdfService  # Import your PDF service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "schedule_id"

    # ✅ Download filtered PDF
    @action(detail=False, methods=["post"])
    def download_filtered_pdf(self, request):
        try:
            addresses_filter = request.data.get("addresses", [])
            
            # Get all pending schedules
            schedules = Schedule.objects.filter(status="Pending").select_related('hotel')
            
            # Generate PDF with filters
            pdf_content = PdfService.generate_pdf(
                schedules=schedules,
                addresses_filter=addresses_filter,
                last_two_days_only=True
            )
            
            # Create filename based on filter
            if addresses_filter:
                filename = f"{'_'.join([addr.replace(' ', '_') for addr in addresses_filter])}_schedules.pdf"
            else:
                filename = "all_hotels_schedules.pdf"
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}")
            return Response(
                {"error": "Failed to generate PDF"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ✅ Update visibility for all schedules of a hotel (by hotel ID)
    @action(detail=False, methods=["patch"])
    def update_visibility_by_hotel(self, request):
        hotel_id = request.data.get("hotel_id")
        is_visible = request.data.get("is_visible", True)

        if not hotel_id:
            return Response({"error": "hotel_id required"}, status=status.HTTP_400_BAD_REQUEST)

        updated = Schedule.objects.filter(hotel__id=hotel_id).update(is_visible=is_visible)
        return Response(
            {"updated": updated, "hotel_id": hotel_id, "is_visible": is_visible},
            status=status.HTTP_200_OK
        )

    # ✅ Send today's apology messages (by hotel ID)
    @action(detail=False, methods=["post"])
    def send_today_message(self, request):
        today_name = datetime.now().strftime('%A')
        hotel_id = request.data.get("hotel_id")

        qs = Schedule.objects.filter(status="Pending", day=today_name)
        if hotel_id:
            qs = qs.filter(hotel__id=hotel_id)

        sent_count = 0
        sent_hotels = []

        for schedule in qs:
            if send_apology_email(schedule, "today"):
                sent_count += 1
                sent_hotels.append(schedule.hotel.name)
                logger.info(f"Today's apology sent to hotel ID {schedule.hotel.hotel_id}: {schedule.hotel.name}")

        return Response(
            {"message": f"{sent_count} apology emails sent for today.", "hotels": sent_hotels},
            status=status.HTTP_200_OK
        )

    # ✅ Send tomorrow's apology messages (by hotel ID)
    @action(detail=False, methods=["post"])
    def send_tomorrow_message(self, request):
        tomorrow_name = (datetime.now() + timedelta(days=1)).strftime('%A')
        hotel_id = request.data.get("hotel_id")

        qs = Schedule.objects.filter(status="Pending", day=tomorrow_name)
        if hotel_id:
            qs = qs.filter(hotel__id=hotel_id)

        sent_count = 0
        sent_hotels = []

        for schedule in qs:
            if send_apology_email(schedule, "tomorrow"):
                sent_count += 1
                sent_hotels.append(schedule.hotel.name)
                logger.info(f"Tomorrow's apology sent to hotel ID {schedule.hotel.hotel_id}: {schedule.hotel.name}")

        return Response(
            {"message": f"{sent_count} apology emails sent for tomorrow.", "hotels": sent_hotels},
            status=status.HTTP_200_OK
        )
        
        
    
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
        Fallback: support query params for inbox/outbox.
        Broadcast messages (recipient=None) appear in inbox.
        """
        recipient_type = self.request.query_params.get("recipient_type")
        recipient_id_str = self.request.query_params.get("recipient_id")
        sender_type = self.request.query_params.get("sender_type")
        sender_id_str = self.request.query_params.get("sender_id")

        # Inbox (direct + broadcasts)
        if recipient_type and recipient_id_str:
            try:
                recipient_id = uuid.UUID(recipient_id_str)
            except ValueError:
                return Notification.objects.none()

            try:
                recipient = (
                    User.objects.get(user_id=recipient_id)
                    if recipient_type == "User"
                    else Client.objects.get(client_id=recipient_id)
                )
            except (User.DoesNotExist, Client.DoesNotExist):
                return Notification.objects.none()

            content_type = ContentType.objects.get_for_model(recipient.__class__)
            return Notification.objects.filter(
                models.Q(
                    recipient_content_type=content_type,
                    recipient_object_id=recipient.pk
                )
                | models.Q(recipient_content_type__isnull=True)  # include broadcasts
            ).order_by("-created_time")

        # Outbox
        if sender_type and sender_id_str:
            try:
                sender_id = uuid.UUID(sender_id_str)
            except ValueError:
                return Notification.objects.none()

            try:
                sender = (
                    User.objects.get(user_id=sender_id)
                    if sender_type == "User"
                    else Client.objects.get(client_id=sender_id)
                )
            except (User.DoesNotExist, Client.DoesNotExist):
                return Notification.objects.none()

            content_type = ContentType.objects.get_for_model(sender.__class__)
            return Notification.objects.filter(
                sender_content_type=content_type,
                sender_object_id=sender.pk
            ).order_by("-created_time")

        return Notification.objects.none()
    
    @csrf_protect
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
            raise serializers.ValidationError(
                "sender_type, sender_id, and message_content are required."
            )

        # Normalize recipient_id for broadcast
        if recipient_id in (None, "", "null"):
            recipient_id = None
            recipient_type = None

        # Resolve sender
        try:
            sender = (
                User.objects.get(user_id=sender_id)
                if sender_type == "User"
                else Client.objects.get(client_id=sender_id)
            )
        except (User.DoesNotExist, Client.DoesNotExist):
            raise serializers.ValidationError({"sender_id": "Invalid sender ID"})

        # Broadcast message
        if recipient_id is None:
            if not isinstance(sender, Client):
                raise serializers.ValidationError(
                    "Only Clients can send broadcast messages"
                )
            serializer.save(
                sender_content_type=ContentType.objects.get_for_model(sender.__class__),
                sender_object_id=sender.pk,
                recipient_content_type=None,
                recipient_object_id=None,
            )
            return

        # Direct message
        if not recipient_type:
            raise serializers.ValidationError(
                {"recipient_type": "recipient_type is required for direct messages"}
            )

        try:
            recipient = (
                User.objects.get(user_id=recipient_id)
                if recipient_type == "User"
                else Client.objects.get(client_id=recipient_id)
            )
        except (User.DoesNotExist, Client.DoesNotExist):
            raise serializers.ValidationError({"recipient_id": "Invalid recipient ID"})

        # Business rules
        if isinstance(sender, Client) and not (
            isinstance(recipient, User) and recipient.role in ["Staff", "Admin"]
        ):
            raise serializers.ValidationError("Clients can only message Staff/Admin")

        if isinstance(sender, User) and sender.role == "Staff" and not isinstance(
            recipient, Client
        ):
            raise serializers.ValidationError("Staff can only message Clients")

        serializer.save(
            sender_content_type=ContentType.objects.get_for_model(sender.__class__),
            sender_object_id=sender.pk,
            recipient_content_type=ContentType.objects.get_for_model(
                recipient.__class__
            ),
            recipient_object_id=recipient.pk,
        )

    @action(detail=False, methods=["get"])
    def inbox(self, request):
        """
        Explicit inbox: includes direct messages and broadcasts.
        GET /api/notifications/inbox/?user_id=<uuid>
        """
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response([], status=400)

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response([], status=404)

        content_type = ContentType.objects.get_for_model(User)
        queryset = Notification.objects.filter(
            models.Q(
                recipient_content_type=content_type,
                recipient_object_id=user.pk
            )
            | models.Q(recipient_content_type__isnull=True)  # broadcasts
        ).order_by("-created_time")

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def outbox(self, request):
        """
        Explicit outbox: all messages sent by this user/client.
        GET /api/notifications/outbox/?user_id=<uuid>
        """
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response([], status=400)

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response([], status=404)

        content_type = ContentType.objects.get_for_model(User)
        queryset = Notification.objects.filter(
            sender_content_type=content_type,
            sender_object_id=user.pk
        ).order_by("-created_time")

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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

        updated_count = Notification.objects.filter(
            notification_id__in=uuids
        ).update(status="Read")
        return Response(
            {"message": f"{updated_count} notification(s) marked as read"},
            status=200,
        )

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


from django.http import FileResponse
from datetime import date, timedelta
from io import BytesIO
from egaz_app.models import Schedule
from .services.pdf_service import PdfService  # hakikisha path hii inalingana na project yako

def download_schedules_pdf(request):
    # Retrieve all pending schedules
    schedules = Schedule.objects.filter(status="Pending").select_related('hotel')

    # Generate PDF: last_two_days_only=True ensures we fetch only today and yesterday
    pdf_bytes = PdfService.generate_pdf(schedules, last_two_days_only=True)

    # Return as file response
    pdf_stream = BytesIO(pdf_bytes)
    return FileResponse(
        pdf_stream,
        as_attachment=True,
        filename="today_yesterday_schedules.pdf",
        content_type="application/pdf"
    )



from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from .models import User, Client, AuthToken, FailedLoginAttempt
import secrets

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"detail": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    # ---1️⃣ Try User login ---
    try:
        user = User.objects.get(email=email)
        failed_tracker, _ = FailedLoginAttempt.objects.get_or_create(user=user)

        if not failed_tracker.can_login():
            remaining = (failed_tracker.locked_until - timezone.now()).seconds // 60 + 1
            return Response(
                {"detail": f"Account locked. Try again in {remaining} minutes."},
                status=status.HTTP_403_FORBIDDEN
            )

        if check_password(password, user.password_hash):
            failed_tracker.reset_attempts()
            # Always create or update token with new value
            token_obj, _ = AuthToken.objects.update_or_create(
                user=user,
                client=None,
                defaults={'token': secrets.token_hex(32)}
            )
            return Response({
                "token": token_obj.token,
                "user": {
                    "id": str(user.user_id),
                    "name": user.name,
                    "email": user.email,
                    "role": user.role
                }
            })
        else:
            failed_tracker.record_failure()
            attempts_left = 3 - failed_tracker.failed_attempts
            return Response(
                {"detail": f"Invalid credentials. Attempts left: {attempts_left}"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except User.DoesNotExist:
        pass

    # --- 2️⃣ Try Client login ---
    try:
        client = Client.objects.get(email=email)
        failed_tracker, _ = FailedLoginAttempt.objects.get_or_create(client=client)

        if not failed_tracker.can_login():
            remaining = (failed_tracker.locked_until - timezone.now()).seconds // 60 + 1
            return Response(
                {"detail": f"Account locked. Try again in {remaining} minutes."},
                status=status.HTTP_403_FORBIDDEN
            )

        if check_password(password, client.password):
            failed_tracker.reset_attempts()
            # Always create or update token with new value
            token_obj, _ = AuthToken.objects.update_or_create(
                user=None,
                client=client,
                defaults={'token': secrets.token_hex(32)}
            )
            return Response({
                "token": token_obj.token,
                "user": {
                    "id": str(client.client_id),
                    "name": client.name,
                    "email": client.email,
                    "role": "client"
                }
            })
        else:
            failed_tracker.record_failure()
            attempts_left = 3 - failed_tracker.failed_attempts
            return Response(
                {"detail": f"Invalid credentials. Attempts left: {attempts_left}"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Client.DoesNotExist:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)



# class AttendanceViewSet(viewsets.ModelViewSet):
#     serializer_class = AttendanceSerializer
#     authentication_classes = [CustomTokenAuthentication]  # <-- Use custom auth
#     permission_classes = [IsAuthenticated]  # Only authenticated users/clients can access

#     def get_queryset(self):
#         return Attendance.objects.all()


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

        result = update_salary_for_all_users(month, year)

        return Response({
            "message": f"Salaries processed successfully",
            "created": result["created"],
            "updated": result["updated"],
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

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import PaymentSlip
from .serializers import PaymentSlipSerializer
from .authentication import CustomTokenAuthentication

class PaymentSlipViewSet(viewsets.ModelViewSet):
    queryset = PaymentSlip.objects.all().select_related('client')
    serializer_class = PaymentSlipSerializer
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field = "slip_id"

    def update(self, request, *args, **kwargs):
        """Allow admin to update receipt, comment, and amount for a payment slip."""
        try:
            slip = self.get_object()
        except PaymentSlip.DoesNotExist:
            return Response({"error": "Payment slip not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update receipt if provided
        receipt = request.FILES.get("receipt")
        if receipt:
            slip.receipt = receipt

        # Update admin comment if provided
        admin_comment = request.data.get("admin_comment")
        if admin_comment is not None:
            slip.admin_comment = admin_comment

        # Update amount if provided
        amount = request.data.get("amount")
        if amount is not None:
            try:
                slip.amount = float(amount)
            except ValueError:
                return Response({"error": "Invalid amount value"}, status=status.HTTP_400_BAD_REQUEST)

        slip.save()
        return Response(
            {
                "message": "Slip updated successfully.",
                "slip_id": str(slip.slip_id),
                "receipt_url": slip.receipt.url if slip.receipt else None,
                "admin_comment": slip.admin_comment,
                "amount": slip.amount,
            },
            status=status.HTTP_200_OK,
        )



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


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PaymentSlip
from .serializers import PaymentSlipSerializer
from .authentication import CustomTokenAuthentication  # your custom auth

class PaymentSlipViewSet(viewsets.ModelViewSet):
    queryset = PaymentSlip.objects.all()
    serializer_class = PaymentSlipSerializer
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a PaymentSlip instance.
        Only fields sent in the request will be updated.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
import os

from .models import MonthlySummary
from .serializers import MonthlySummarySerializer
from .authentication import CustomTokenAuthentication

class MonthlySummaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for overall monthly summary of all hotels combined.
    """
    queryset = MonthlySummary.objects.all()
    serializer_class = MonthlySummarySerializer
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # --- Generate monthly summary (POST) ---
    @action(detail=False, methods=['post'], url_path='generate_summaries')
    def generate_summaries(self, request):
        month_str = request.data.get('month')
        if not month_str:
            return Response({"error": "Month is required (YYYY-MM)."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, month = map(int, month_str.split('-'))
            month_date = datetime(year, month, 1).date()
        except ValueError:
            return Response({"error": "Invalid month format. Use YYYY-MM."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            summary = MonthlySummary.generate_for_month(month_date)
        except Exception as e:
            return Response({"error": f"Failed to generate monthly summary: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.get_serializer(summary)
        return Response({
            "message": f"Monthly summary generated for {month_date.strftime('%B %Y')}",
            "summary": serializer.data
        }, status=status.HTTP_200_OK)

    # --- Fetch monthly summary (GET) ---
    @action(detail=False, methods=['get'], url_path='month_summary')
    def month_summary(self, request):
        month_str = request.query_params.get('month')
        if not month_str:
            return Response({"error": "Month is required (YYYY-MM)."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, month = map(int, month_str.split('-'))
            month_date = datetime(year, month, 1).date()
        except ValueError:
            return Response({"error": "Invalid month format. Use YYYY-MM."}, status=status.HTTP_400_BAD_REQUEST)

        summaries = MonthlySummary.objects.filter(month=month_date)
        serializer = self.get_serializer(summaries, many=True)
        return Response({"summaries": serializer.data}, status=status.HTTP_200_OK)

    # --- Update monthly summary (PATCH) ---
    def partial_update(self, request, *args, **kwargs):
        """
        Update processed totals or upload report files.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to update summary: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
# views.py - ADD THESE SEPARATE VIEWS
from django.http import HttpResponse
from datetime import datetime
from .reports.waste_report import generate_waste_pdf
from .reports.payment_report import generate_payment_pdf

def download_waste_report(request):
    """Working waste report download"""
    month_str = request.GET.get("month")
    if not month_str:
        return HttpResponse("Month parameter is required", status=400)
    
    try:
        month = datetime.strptime(month_str, "%Y-%m").date().replace(day=1)
    except ValueError:
        return HttpResponse("Invalid month format. Use YYYY-MM", status=400)

    pdf_buffer = generate_waste_pdf(month)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="waste_report_{month_str}.pdf"'
    return response

def download_payment_report(request):
    """Working payment report download"""
    month_str = request.GET.get("month")
    if not month_str:
        return HttpResponse("Month parameter is required", status=400)
    
    try:
        month = datetime.strptime(month_str, "%Y-%m").date().replace(day=1)
    except ValueError:
        return HttpResponse("Invalid month format. Use YYYY-MM", status=400)

    pdf_buffer = generate_payment_pdf(month)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payment_report_{month_str}.pdf"'
    return response




from django.http import HttpResponse
from datetime import datetime
from .reports.waste_report import generate_waste_pdf
from .reports.payment_report import generate_payment_pdf

def download_waste_report(request):
    month_str = request.GET.get("month")  # expect YYYY-MM
    if not month_str:
        return HttpResponse("Month parameter is required", status=400)
    
    try:
        month = datetime.strptime(month_str, "%Y-%m").date().replace(day=1)
    except ValueError:
        return HttpResponse("Invalid month format. Use YYYY-MM", status=400)

    pdf_buffer = generate_waste_pdf(month)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="waste_report_{month_str}.pdf"'
    return response

def download_payment_report(request):
    month_str = request.GET.get("month")  # expect YYYY-MM
    if not month_str:
        return HttpResponse("Month parameter is required", status=400)
    
    try:
        month = datetime.strptime(month_str, "%Y-%m").date().replace(day=1)
    except ValueError:
        return HttpResponse("Invalid month format. Use YYYY-MM", status=400)

    pdf_buffer = generate_payment_pdf(month)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payment_report_{month_str}.pdf"'
    return response

from rest_framework import viewsets, serializers
from rest_framework.permissions import AllowAny
from django.db.models import Q
from .models import PaidHotelInfo, MonthlySummary
from .serializers import PaidHotelInfoSerializer, PublicMonthlySummarySerializer

# ------------------------------
# Public Hotel Info ViewSet - ✅ SAWA
# ------------------------------
class PublicHotelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaidHotelInfo.objects.all()
    serializer_class = PaidHotelInfoSerializer
    permission_classes = [AllowAny]


# ------------------------------
# Public Monthly Summary ViewSet - ✅ SAWA
# ------------------------------
class PublicMonthlySummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MonthlySummary.objects.all()
    serializer_class = PublicMonthlySummarySerializer
    permission_classes = [AllowAny]


# ------------------------------
# Public Document Serializer - 🔥 FIX THIS PART
# ------------------------------
class PublicDocumentSerializer(serializers.ModelSerializer):
    month_display = serializers.SerializerMethodField()
    waste_report_url = serializers.SerializerMethodField()  # ✅ CORRECT NAME
    payment_report_url = serializers.SerializerMethodField()  # ✅ CORRECT NAME

    class Meta:
        model = MonthlySummary
        fields = [
            "month",
            "month_display",
            "waste_report_url",  # ✅ CORRECT FIELD NAME
            "payment_report_url",  # ✅ CORRECT FIELD NAME
        ]

    def get_month_display(self, obj):
        return obj.month.strftime("%B %Y") if obj.month else ""

    def get_waste_report_url(self, obj):  # ✅ CORRECT METHOD NAME
        return obj.get_waste_report_url()

    def get_payment_report_url(self, obj):  # ✅ CORRECT METHOD NAME
        return obj.get_payment_report_url()


# ------------------------------
# Public Document ViewSet - ✅ SAWA
# ------------------------------
class PublicDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicDocumentSerializer  # 🔥 NOW IT WILL WORK
    permission_classes = [AllowAny]

    def get_queryset(self):
        return MonthlySummary.objects.filter(
            Q(processed_waste_report__isnull=False) |
            Q(processed_payment_report__isnull=False)
        ).order_by('-month')
        
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import HttpResponse
from datetime import datetime
import os
import uuid
import zipfile
from io import BytesIO

from egaz_app.models import Invoice, Hotel, Client
from egaz_app.serializers import InvoiceSerializer
from egaz_app.services.email_service import send_invoice_to_both_parties


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
       
    @action(detail=False, methods=['post'])
    def generate_for_month(self, request):
        """
        Generate invoices for all hotels for the given month/year.
        IMPORTANT:
        - If hotel has NO client → invoice.client = None
        """
        month_str = request.data.get("month")
        if not month_str:
            return Response({"detail": "Month is required."}, status=status.HTTP_400_BAD_REQUEST)
    
        try:
            dt = datetime.strptime(month_str, "%Y-%m")
            month = dt.month
            year = dt.year
        except ValueError:
            return Response({"detail": "Invalid month format. Use YYYY-MM."}, status=status.HTTP_400_BAD_REQUEST)

        hotels = Hotel.objects.all()
        created_count = 0

        for hotel in hotels:

            invoice, created = Invoice.objects.get_or_create(
                hotel=hotel,
                month=month,
                year=year,
                defaults={
                    "client": hotel.client if hotel.client else None,   # 🔥 FIXED
                    "status": "not_sent",
                    "files": []
                }
            )

            # If invoice exists but client is missing, update it
            if not created and invoice.client is None and hotel.client:
                invoice.client = hotel.client
                invoice.save()

            if created:
                created_count += 1

        return Response(
            {"detail": f"{created_count} invoices generated for {month_str}"},
            status=status.HTTP_201_CREATED
        )

    # 🔥 UPLOAD FILES - NO SIZE LIMITS
    @action(detail=True, methods=['post'])
    def upload_files(self, request, pk=None):
        invoice = self.get_object()
        uploaded_files = request.FILES.getlist('files')
        
        if not uploaded_files:
            return Response({"detail": "No files provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        saved_files = []
        
        for file in uploaded_files:
            file_extension = os.path.splitext(file.name)[1]
            unique_filename = f"invoices/{uuid.uuid4()}{file_extension}"
            file_path = default_storage.save(unique_filename, ContentFile(file.read()))
            file_url = request.build_absolute_uri(default_storage.url(file_path))
            
            file_info = {
                'id': str(uuid.uuid4()),
                'name': file.name,
                'url': file_url,
                'uploaded_at': datetime.now().isoformat()
            }
            
            if not invoice.files:
                invoice.files = []
            
            invoice.files.append(file_info)
            saved_files.append(file_info)
        
        invoice.save()
        
        return Response({
            "message": f"Successfully uploaded {len(saved_files)} files",
            "uploaded_files": saved_files,
            "total_files": len(invoice.files)
        }, status=status.HTTP_201_CREATED)

    # 🔥 REMOVE FILE
    @action(detail=True, methods=['post'])
    def remove_file(self, request, pk=None):
        invoice = self.get_object()
        file_id = request.data.get('file_id')
        
        if not file_id:
            return Response({"detail": "File ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not invoice.files:
            return Response({"detail": "No files to remove."}, status=status.HTTP_400_BAD_REQUEST)
        
        file_to_remove = None
        updated_files = []
        
        for file_info in invoice.files:
            if file_info.get('id') == file_id:
                file_to_remove = file_info
            else:
                updated_files.append(file_info)
        
        if file_to_remove:
            try:
                if 'media/' in file_to_remove.get('url'):
                    file_path = file_to_remove.get('url').split('media/')[-1]
                else:
                    file_path = file_to_remove.get('url').split('/media/')[-1]
                default_storage.delete(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
            
            invoice.files = updated_files
            invoice.save()
            
            return Response({
                "message": f"File '{file_to_remove.get('name')}' removed successfully",
                "remaining_files": len(invoice.files)
            }, status=status.HTTP_200_OK)
        
        return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

    # 🔥 SEND INVOICE
    @action(detail=True, methods=['post'])
    def send_invoice(self, request, pk=None):
        invoice = self.get_object()

        if not invoice.files:
            return Response({
                "detail": "Cannot send invoice without files. Please upload files first."
            }, status=status.HTTP_400_BAD_REQUEST)

        invoice.status = 'sent'
        invoice.save()

        # Only send emails if invoice has a client
        if invoice.client:
            email_results = send_invoice_to_both_parties(invoice, request)
        else:
            email_results = "Invoice has no client assigned"

        return Response({
            'message': 'Invoice sent successfully.',
            'status': invoice.status,
            'files_count': len(invoice.files),
            'emails_sent': email_results
        }, status=status.HTTP_200_OK)

    # 🔥 BULK SEND INVOICES
    @action(detail=False, methods=['post'])
    def bulk_send(self, request):
        invoice_ids = request.data.get('invoice_ids', [])
        results = []
        
        for invoice_id in invoice_ids:
            try:
                invoice = Invoice.objects.get(invoice_id=invoice_id)
                
                if not invoice.files:
                    results.append({
                        'invoice_id': str(invoice.invoice_id),
                        'hotel': invoice.hotel.name,
                        'error': 'No files uploaded'
                    })
                    continue
                
                invoice.status = 'sent'
                invoice.save()
                
                if invoice.client:
                    email_results = send_invoice_to_both_parties(invoice, request)
                else:
                    email_results = "Invoice has no client assigned"
                
                results.append({
                    'invoice_id': str(invoice.invoice_id),
                    'hotel': invoice.hotel.name,
                    'files_count': len(invoice.files),
                    'emails_sent': email_results,
                    'status': 'sent'
                })
                
            except Invoice.DoesNotExist:
                results.append({'invoice_id': invoice_id, 'error': 'Invoice not found'})
            except Exception as e:
                results.append({'invoice_id': invoice_id, 'error': str(e)})
        
        return Response({
            'message': f'Processed {len(results)} invoices',
            'results': results
        }, status=status.HTTP_200_OK)

    # 🔥 MARK RECEIVED
    @action(detail=True, methods=['post'])
    def mark_received(self, request, pk=None):
        invoice = self.get_object()
        comment = request.data.get("comment", "")

        invoice.is_received = True
        invoice.status = 'received'
        if comment:
            invoice.comment = comment
        invoice.save()

        return Response({
            "message": "Invoice marked as received",
            "files_count": len(invoice.files)
        }, status=status.HTTP_200_OK)

    # 🔥 ZIP DOWNLOAD
    @action(detail=True, methods=['get'])
    def download_files(self, request, pk=None):
        invoice = self.get_object()
        
        if not invoice.files:
            return Response({"detail": "No files available for download."}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for file_info in invoice.files:
                try:
                    if 'media/' in file_info.get('url'):
                        file_path = file_info.get('url').split('media/')[-1]
                    else:
                        file_path = file_info.get('url').split('/media/')[-1]
                    
                    if default_storage.exists(file_path):
                        file_content = default_storage.open(file_path).read()
                        zip_file.writestr(file_info.get('name'), file_content)
                except Exception as e:
                    print(f"Error reading file {file_info.get('name')}: {e}")
                    continue
        
        zip_buffer.seek(0)
        
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = (
            f'attachment; filename="invoice_files_{invoice.hotel.name}_{invoice.month}_{invoice.year}.zip"'
        )
        return response

    # 🔥 GET SINGLE FILE
    @action(detail=True, methods=['get'])
    def get_file(self, request, pk=None):
        invoice = self.get_object()
        file_id = request.query_params.get('file_id')
        
        if not file_id:
            return Response({"detail": "File ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        file_info = None
        for f in invoice.files:
            if f.get('id') == file_id:
                file_info = f
                break
        
        if not file_info:
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            if 'media/' in file_info.get('url'):
                file_path = file_info.get('url').split('media/')[-1]
            else:
                file_path = file_info.get('url').split('/media/')[-1]
            
            if default_storage.exists(file_path):
                file_content = default_storage.open(file_path).read()
                response = HttpResponse(file_content, content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{file_info.get("name")}"'
                return response
            else:
                return Response({"detail": "File not found in storage."}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({"detail": f"Error retrieving file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 🔥 UPDATE STATUS
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        invoice = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)

        invoice.status = new_status
        invoice.save()
        
        if new_status == 'sent' and invoice.files and invoice.client:
            email_results = send_invoice_to_both_parties(invoice, request)
            return Response({
                'message': f'Status changed to {new_status} and notifications sent.',
                'emails_sent': email_results
            }, status=status.HTTP_200_OK)
        
        return Response({'message': f'Status changed to {new_status}'}, status=status.HTTP_200_OK)

    # 🔥 STATS
    @action(detail=False, methods=['get'])
    def stats(self, request):
        total_invoices = Invoice.objects.count()
        sent_invoices = Invoice.objects.filter(status='sent').count()
        received_invoices = Invoice.objects.filter(status='received').count()
        invoices_with_files = Invoice.objects.exclude(files=[]).count()
        
        return Response({
            'total_invoices': total_invoices,
            'sent_invoices': sent_invoices,
            'received_invoices': received_invoices,
            'invoices_with_files': invoices_with_files
        }, status=status.HTTP_200_OK)
        
        
        
        
        
        
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
import os

from .models import Storage, User  # Make sure to import User model
from .serializers import StorageSerializer

class StorageViewSet(viewsets.ModelViewSet):
    queryset = Storage.objects.all()
    serializer_class = StorageSerializer

    def get_queryset(self):
        # Users can only see their own documents
        # Extract the actual user instance from the wrapper
        user = self.get_actual_user()
        return Storage.objects.filter(uploaded_by=user)

    def perform_create(self, serializer):
        # Extract the actual user instance from the wrapper
        user = self.get_actual_user()
        serializer.save(uploaded_by=user)

    def get_actual_user(self):
        """
        Extract the actual User instance from the DRFUserWrapper
        """
        user_obj = self.request.user
        
        # If it's a wrapper, get the underlying user object
        if hasattr(user_obj, '_obj'):
            return user_obj._obj
        return user_obj

    # 🔥 GET /api/storage/by_type/?type={type} - Filter by document type
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get documents filtered by type"""
        document_type = request.query_params.get('type')
        if document_type:
            user = self.get_actual_user()
            documents = Storage.objects.filter(uploaded_by=user, document_type=document_type)
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data)
        return Response({"detail": "Type parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    # 🔥 GET /api/storage/search/?q={query} - Search documents
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search documents by name or description"""
        query = request.query_params.get('q')
        if query:
            user = self.get_actual_user()
            documents = Storage.objects.filter(
                Q(uploaded_by=user) &
                (Q(name__icontains=query) | Q(description__icontains=query))
            )
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data)
        return Response({"detail": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

    # 🔥 GET /api/storage/{document_id}/download/ - Download document file
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the document file"""
        document = self.get_object()
        
        if document.file:
            response = FileResponse(
                document.file.open('rb'),
                content_type=document.get_mime_type(),
                filename=f"{document.name}.{document.file_extension}"
            )
            response['Content-Disposition'] = f'attachment; filename="{document.name}.{document.file_extension}"'
            return response
        
        return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

    # 🔥 GET /api/storage/{document_id}/preview/ - Preview document
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Preview document in browser (for supported file types)"""
        document = self.get_object()
        
        if not document.can_preview():
            return Response(
                {"detail": "This file type cannot be previewed in browser."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if document.file:
            response = FileResponse(
                document.file.open('rb'),
                content_type=document.get_mime_type()
            )
            response['Content-Disposition'] = f'inline; filename="{document.name}.{document.file_extension}"'
            return response
        
        return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

    # 🔥 GET /api/storage/stats/ - Get storage statistics
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get storage statistics"""
        user = self.get_actual_user()
        user_documents = Storage.objects.filter(uploaded_by=user)
        total_documents = user_documents.count()
        total_size = sum(doc.file_size for doc in user_documents)
        
        # Documents by type
        by_type = {}
        for doc_type, _ in Storage.DOCUMENT_TYPES:
            count = user_documents.filter(document_type=doc_type).count()
            by_type[doc_type] = count
        
        # Documents by category
        by_category = {}
        categories = ['document', 'spreadsheet', 'presentation', 'image', 'archive', 'other']
        for category in categories:
            count = user_documents.filter(file_type_category=category).count()
            by_category[category] = count
        
        return Response({
            'total_documents': total_documents,
            'total_size': total_size,
            'total_size_display': self.format_file_size(total_size),
            'documents_by_type': by_type,
            'documents_by_category': by_category
        })

    # 🔥 GET /api/storage/categories/ - Get document categories
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available document categories"""
        categories = [
            {'value': 'document', 'label': 'Documents', 'icon': '📝'},
            {'value': 'spreadsheet', 'label': 'Spreadsheets', 'icon': '📊'},
            {'value': 'presentation', 'label': 'Presentations', 'icon': '📑'},
            {'value': 'image', 'label': 'Images', 'icon': '🖼️'},
            {'value': 'archive', 'label': 'Archives', 'icon': '📦'},
            {'value': 'other', 'label': 'Other', 'icon': '📎'}
        ]
        return Response(categories)

    # 🔥 GET /api/storage/types/ - Get document types
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available document types"""
        types_list = [
            {'value': type_value, 'label': type_label}
            for type_value, type_label in Storage.DOCUMENT_TYPES
        ]
        return Response(types_list)

    def format_file_size(self, size_bytes):
        """Format file size for display"""
        if size_bytes == 0:
            return "0 Bytes"
        
        size_names = ['Bytes', 'KB', 'MB', 'GB']
        i = 0
        size = size_bytes
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
            
        return f"{size:.2f} {size_names[i]}"
    
# clients/views_client.py - For client self-management
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password, make_password  # Add make_password import

from .models import Client
from .serializers import ClientProfileSerializer, ClientPasswordChangeSerializer

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def client_profile(request):
    """
    Client can view and update their own profile
    """
    try:
        # Assuming the authenticated user is a Client instance
        client = request.user
        
        if request.method == 'GET':
            serializer = ClientProfileSerializer(client)
            return Response(serializer.data)
            
        elif request.method == 'PUT':
            serializer = ClientProfileSerializer(client, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": "Profile updated successfully",
                    "client": serializer.data
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Client.DoesNotExist:
        return Response(
            {"error": "Client not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Client can change their password
    """
    try:
        client = request.user
        serializer = ClientPasswordChangeSerializer(data=request.data)
        
        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            
            # Verify current password
            if not check_password(current_password, client.password):
                return Response(
                    {"error": "Current password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # FIX: Use make_password instead of set_password
            client.password = make_password(new_password)
            client.save()
            
            return Response({"message": "Password changed successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Client.DoesNotExist:
        return Response(
            {"error": "Client not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"Error in change_password: {str(e)}")  # Add debug logging
        return Response(
            {"error": "Internal server error. Please try again."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_dashboard(request):
    """
    Get client dashboard data
    """
    try:
        client = request.user
        
        # Add any dashboard data you want to return
        dashboard_data = {
            "client_name": client.name,
            "email": client.email,
            "phone": client.phone,
            "client_id": client.client_id,
            "total_orders": 0,  # Add your logic here
            "pending_orders": 0, # Add your logic here
            "recent_activity": [] # Add your logic here
        }
        return Response(dashboard_data)
        
    except Client.DoesNotExist:
        return Response(
            {"error": "Client not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )