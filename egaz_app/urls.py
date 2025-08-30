from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'hotels', HotelViewSet)
router.register(r'pending-hotels', PendingHotelViewSet)
router.register(r'users', UserViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'waste-types', WasteTypeViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'work-shifts', WorkShiftViewSet)
router.register(r'attendance-records', AttendanceRecordViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'completed-waste-records', CompletedWasteRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
