from django.contrib import admin
from django.urls import path, include, re_path
from egaz_app import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path("download-schedules/", views.download_schedules_pdf, name="download_schedules_pdf"),
    path("login/", views.login_view, name="login"),
    path("payment-slips/<uuid:slip_id>/view/", views.view_payment_slip, name="view_payment_slip"),
    path('api/', include('egaz_app.urls')),
]

# 🔥 DOUBLE PROTECTION - Works in both development and production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]