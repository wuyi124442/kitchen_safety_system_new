
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# 创建超级用户（如果不存在）
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("超级用户创建成功: admin/admin123")
else:
    print("超级用户已存在")
