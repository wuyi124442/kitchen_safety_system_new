"""
URL configuration for Kitchen Safety Detection System Django app.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('auth/', include('kitchen_safety_system.web.django_app.apps.authentication.urls')),
    path('dashboard/', include('kitchen_safety_system.web.django_app.apps.monitoring.urls')),
    path('alerts/', include('kitchen_safety_system.web.django_app.apps.alerts.urls')),
    path('config/', include('kitchen_safety_system.web.django_app.apps.configuration.urls')),
    path('logs/', include('kitchen_safety_system.web.django_app.apps.logs.urls')),
    path('api/', include('kitchen_safety_system.web.django_app.api.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)