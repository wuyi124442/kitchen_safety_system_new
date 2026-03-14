from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    # Web views
    path('', views.AlertListView.as_view(), name='list'),
    path('<int:pk>/', views.AlertDetailView.as_view(), name='detail'),
    path('<int:pk>/action/', views.alert_action, name='action'),
    
    # API views
    path('api/list/', views.api_alert_list, name='api_list'),
    path('api/<int:pk>/', views.api_alert_detail, name='api_detail'),
    path('api/statistics/', views.api_alert_statistics, name='api_statistics'),
]