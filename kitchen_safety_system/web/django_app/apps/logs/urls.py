from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    # Web界面
    path('', views.log_query_page, name='log_query'),
    path('monitor/', views.log_monitor_page, name='log_monitor'),
    
    # API endpoints
    path('api/logs/', views.log_list, name='log_list'),
    path('api/logs/<int:log_id>/', views.log_detail, name='log_detail'),
    path('api/logs/export/', views.log_export, name='log_export'),
    path('api/logs/statistics/', views.log_statistics, name='log_statistics'),
    path('api/logs/realtime/', views.log_realtime, name='log_realtime'),
]