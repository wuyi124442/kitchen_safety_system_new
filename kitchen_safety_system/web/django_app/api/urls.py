from django.urls import path, include

app_name = 'api'

urlpatterns = [
    path('auth/', include('kitchen_safety_system.web.django_app.apps.authentication.urls')),
    path('monitoring/', include('kitchen_safety_system.web.django_app.apps.monitoring.urls')),
    path('alerts/', include('kitchen_safety_system.web.django_app.apps.alerts.urls')),
    path('config/', include('kitchen_safety_system.web.django_app.apps.configuration.urls')),
]