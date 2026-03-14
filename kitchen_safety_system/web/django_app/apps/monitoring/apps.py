from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kitchen_safety_system.web.django_app.apps.monitoring'
    verbose_name = '系统监控'