from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    # Web views
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # API views
    path('api/system-status/', views.api_system_status, name='api_system_status'),
    path('api/detection-statistics/', views.api_detection_statistics, name='api_detection_statistics'),
    path('api/performance-metrics/', views.api_performance_metrics, name='api_performance_metrics'),
    path('api/dashboard-summary/', views.api_dashboard_summary, name='api_dashboard_summary'),
]