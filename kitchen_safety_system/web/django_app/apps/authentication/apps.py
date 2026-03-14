from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kitchen_safety_system.web.django_app.apps.authentication'
    verbose_name = '用户认证'