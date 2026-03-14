#!/bin/bash
# Django Web界面启动脚本

echo "启动厨房安全检测系统Web界面..."

# 设置环境变量
export DJANGO_SETTINGS_MODULE=kitchen_safety_system.web.django_app.settings
export DATABASE_ENGINE=sqlite3
export DATABASE_NAME=kitchen_safety.db
export DJANGO_DEBUG=True

# 进入Django目录
cd kitchen_safety_system/web/django_app

# 应用数据库迁移
echo "应用数据库迁移..."
python manage.py migrate

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput

# 启动开发服务器
echo "启动Django开发服务器..."
echo "Web界面地址: http://127.0.0.1:8000"
echo "管理后台地址: http://127.0.0.1:8000/admin"
echo "默认管理员账号: admin/admin123"
python manage.py runserver 127.0.0.1:8000
