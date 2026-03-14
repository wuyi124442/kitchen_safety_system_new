from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Web views
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # API views
    path('api/login/', views.APILoginView.as_view(), name='api_login'),
    path('api/logout/', views.api_logout_view, name='api_logout'),
    path('api/user-info/', views.api_user_info, name='api_user_info'),
]