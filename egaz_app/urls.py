from django.urls import path, include
from rest_framework import routers
from .views import *
from . import views

router = routers.DefaultRouter()
router.register(r'hotels', HotelViewSet)
router.register(r'pending-hotels', PendingHotelViewSet)
router.register(r'users', UserViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'waste-types', WasteTypeViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'work-shifts', WorkShiftViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'completed-waste-records', CompletedWasteRecordViewSet)
router.register(r'payment-slips', PaymentSlipViewSet, basename='paymentslip')

# Salary & Attendance
router.register(r'salary/users-with-salaries', UserWithSalaryViewSet, basename='user-with-salary')
router.register(r'salary/role-salary-policies', RoleSalaryPolicyViewSet, basename='role-salary-policy')
router.register(r'salary/attendance', AttendanceViewSet, basename='attendance')
router.register(r'salary/salaries', SalaryViewSet, basename='salary')
router.register(r'paid-hotels', PaidHotelInfoViewSet, basename='paid-hotel')
router.register(r'user-notifications', UserNotificationViewSet, basename='user-notifications')
router.register(r'monthly-summaries', MonthlySummaryViewSet, basename='monthly-summary')


router.register(r'public/hotels', PublicHotelViewSet, basename='public-hotels')
router.register(r'public/monthly-summary', PublicMonthlySummaryViewSet, basename='public-monthly-summary')
router.register(r'public/documents', PublicDocumentViewSet, basename='public-documents')

router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('', include(router.urls)),
    path("reports/waste/", views.download_waste_report, name="waste_report"),
    path("reports/payment/", views.download_payment_report, name="payment_report"),
]
