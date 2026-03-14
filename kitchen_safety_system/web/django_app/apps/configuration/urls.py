from django.urls import path
from . import views

app_name = 'configuration'

urlpatterns = [
    # Web views - System Configuration
    path('', views.ConfigurationListView.as_view(), name='list'),
    path('edit/<int:pk>/', views.ConfigurationUpdateView.as_view(), name='edit'),
    
    # Web views - Detection Thresholds
    path('thresholds/', views.DetectionThresholdListView.as_view(), name='thresholds'),
    path('thresholds/edit/<int:pk>/', views.DetectionThresholdUpdateView.as_view(), name='threshold_edit'),
    
    # Web views - Camera Configuration
    path('cameras/', views.CameraConfigurationListView.as_view(), name='cameras'),
    path('cameras/add/', views.CameraConfigurationCreateView.as_view(), name='camera_add'),
    path('cameras/edit/<int:pk>/', views.CameraConfigurationUpdateView.as_view(), name='camera_edit'),
    
    # API views
    path('api/config/<str:key>/', views.api_get_configuration, name='api_get_config'),
    path('api/config/<str:key>/update/', views.api_update_configuration, name='api_update_config'),
    path('api/configs/', views.api_get_all_configurations, name='api_get_all_configs'),
    path('api/configs/update/', views.api_update_all_configurations, name='api_update_all_configs'),
    path('api/thresholds/', views.api_get_detection_thresholds, name='api_get_thresholds'),
    path('api/cameras/', views.api_get_camera_configurations, name='api_get_cameras'),
    path('api/upload-video/', views.api_upload_video, name='api_upload_video'),
]