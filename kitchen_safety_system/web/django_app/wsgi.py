"""
WSGI config for Kitchen Safety Detection System Django app.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings')

application = get_wsgi_application()