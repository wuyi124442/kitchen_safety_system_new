from django.apps import AppConfig


class ConfigurationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kitchen_safety_system.web.django_app.apps.configuration'
    verbose_name = '系统配置'