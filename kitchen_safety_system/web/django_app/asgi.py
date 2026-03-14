"""
ASGI config for Kitchen Safety Detection System Django app.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings')

application = get_asgi_application()