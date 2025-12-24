# urls.py
from django.urls import path, include
from rest_framework import routers
from .views import *
from . import views

router = routers.DefaultRouter()
router.register(r'hotels', HotelViewSet)
router.register(r'pending-hotels', PendingHotelViewSet)
router.register(r'users', UserViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'clients-management', ClientManagementViewSet, basename='client-management')
router.register(r'waste-types', WasteTypeViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'work-shifts', WorkShiftViewSet)
router.register(r'schedules', ScheduleViewSet)  # ✅ HII IMOJA TUU
router.register(r'notifications', NotificationViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'completed-waste-records', CompletedWasteRecordViewSet)
router.register(r'payment-slips', PaymentSlipViewSet, basename='paymentslip')
router.register(r'storage', StorageViewSet, basename='storage')

# Salary & Attendance
router.register(r'salary/users-with-salaries', UserWithSalaryViewSet, basename='user-with-salary')
router.register(r'salary/role-salary-policies', RoleSalaryPolicyViewSet, basename='role-salary-policy')
router.register(r'salary/attendance', AttendanceViewSet, basename='attendance')
router.register(r'salary/salaries', SalaryViewSet, basename='salary')
router.register(r'paid-hotels', PaidHotelInfoViewSet, basename='paid-hotel')
router.register(r'user-notifications', UserNotificationViewSet, basename='user-notifications')

# 🔥 FIXED: MonthlySummary with proper basename
router.register(r'monthly-summaries', MonthlySummaryViewSet, basename='monthly-summary')

router.register(r'public/hotels', PublicHotelViewSet, basename='public-hotels')
router.register(r'public/monthly-summary', PublicMonthlySummaryViewSet, basename='public-monthly-summary')
router.register(r'public/documents', PublicDocumentViewSet, basename='public-documents')

# Invoices
router.register(r'invoices', InvoiceViewSet, basename='invoice')

# Additional schedule endpoints for auto-generation
urlpatterns = [
    path('', include(router.urls)),
    
    # 🔥 OLD: Legacy report endpoints (keep for backward compatibility)
    path("reports/waste/", views.download_waste_report, name="waste_report"),
    path("reports/payment/", views.download_payment_report, name="payment_report"),
    
    # 🔥 NEW: Auto-scheduler endpoints
    path('schedules/weekly-overview/', 
         ScheduleViewSet.as_view({'get': 'weekly_overview'}), 
         name='weekly-overview'),
    path('schedules/by-week-type/', 
         ScheduleViewSet.as_view({'get': 'by_week_type'}), 
         name='by-week-type'),
    path('schedules/initialize-system/', 
         ScheduleViewSet.as_view({'post': 'initialize_system'}), 
         name='initialize-system'),
    path('schedules/cleanup-old/', 
         ScheduleViewSet.as_view({'post': 'cleanup_old'}), 
         name='cleanup-old'),
    path('schedules/system-status/', 
         ScheduleViewSet.as_view({'get': 'system_status'}), 
         name='system-status'),
]