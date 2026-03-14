# 厨房安全检测系统 - Django Web后台

## 概述

Django Web后台为厨房安全检测系统提供了完整的管理界面，包括用户认证、系统监控、报警管理和配置管理功能。

## 功能特性

### 1. 用户认证和权限管理
- 用户登录、注册和权限控制
- 管理员和普通用户角色区分
- 个人配置管理

### 2. 系统监控仪表板
- 实时系统状态显示
- 检测统计和性能指标
- 图表展示和数据可视化

### 3. 报警历史管理
- 报警记录列表和详情页面
- 多条件筛选和分页功能
- 报警确认和解决操作

### 4. 系统配置管理
- 检测阈值配置页面
- 实时配置更新功能
- 摄像头配置管理

## 技术架构

- **Web框架**: Django 4.2+
- **REST API**: Django REST Framework
- **数据库**: PostgreSQL
- **缓存**: Redis
- **前端**: Bootstrap 5 + Chart.js
- **认证**: Django内置认证系统

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置以下环境变量：

```bash
# Django配置
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your-secret-key

# 数据库配置
DB_NAME=kitchen_safety_db
DB_USER=kitchen_safety_user
DB_PASSWORD=kitchen_safety_password
DB_HOST=localhost
DB_PORT=5432

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. 启动服务

使用启动脚本：

```bash
python kitchen_safety_system/web/start_django.py
```

或手动启动：

```bash
cd kitchen_safety_system/web/django_app
python manage.py migrate
python manage.py init_system
python manage.py runserver
```

### 4. 访问系统

- Web界面: http://localhost:8000
- 管理后台: http://localhost:8000/admin/
- API文档: http://localhost:8000/api/

默认管理员账户：
- 用户名: admin
- 密码: admin123

## API接口

### 认证接口
- `POST /auth/api/login/` - 用户登录
- `POST /auth/api/logout/` - 用户登出
- `GET /auth/api/user-info/` - 获取用户信息

### 监控接口
- `GET /dashboard/api/system-status/` - 获取系统状态
- `GET /dashboard/api/detection-statistics/` - 获取检测统计
- `GET /dashboard/api/performance-metrics/` - 获取性能指标
- `GET /dashboard/api/dashboard-summary/` - 获取仪表板摘要

### 报警接口
- `GET /alerts/api/list/` - 获取报警列表
- `GET /alerts/api/{id}/` - 获取报警详情
- `GET /alerts/api/statistics/` - 获取报警统计

### 配置接口
- `GET /config/api/configs/` - 获取所有配置
- `GET /config/api/config/{key}/` - 获取单个配置
- `POST /config/api/config/{key}/update/` - 更新配置
- `GET /config/api/thresholds/` - 获取检测阈值
- `GET /config/api/cameras/` - 获取摄像头配置

## 数据模型

### 用户模型
- User: 扩展的用户模型，包含角色和部门信息
- UserProfile: 用户配置文件

### 监控模型
- SystemStatus: 系统状态记录
- DetectionStatistics: 检测统计信息
- PerformanceMetrics: 性能指标记录

### 报警模型
- Alert: 报警记录
- AlertRule: 报警规则配置
- NotificationLog: 通知发送日志

### 配置模型
- SystemConfiguration: 系统配置
- DetectionThreshold: 检测阈值
- CameraConfiguration: 摄像头配置
- ConfigurationHistory: 配置变更历史

## 集成说明

Django后台通过 `django_integration.py` 模块与主检测系统集成：

```python
from kitchen_safety_system.web.django_integration import django_integration

# 创建报警
alert = django_integration.create_alert(
    alert_type='fall',
    title='检测到人员跌倒',
    description='在厨房区域检测到人员跌倒',
    severity='high',
    confidence=0.95
)

# 更新系统状态
django_integration.update_system_status({
    'status': 'running',
    'cpu_usage': 45.2,
    'memory_usage': 62.1,
    'detection_fps': 28.5,
    'active_cameras': 2
})

# 获取配置
config = django_integration.get_system_configuration('detection.fall_confidence_threshold')
```

## 部署说明

### 开发环境
使用Django开发服务器：
```bash
python kitchen_safety_system/web/start_django.py
```

### 生产环境
使用Gunicorn + Nginx：

1. 安装Gunicorn:
```bash
pip install gunicorn
```

2. 启动Gunicorn:
```bash
cd kitchen_safety_system/web/django_app
gunicorn kitchen_safety_system.web.django_app.wsgi:application --bind 0.0.0.0:8000
```

3. 配置Nginx反向代理

### Docker部署
参考项目根目录的 `docker-compose.yml` 文件。

## 开发指南

### 添加新的API接口
1. 在相应的app中创建视图函数
2. 在urls.py中添加URL路由
3. 更新API文档

### 添加新的配置项
1. 使用Django管理后台添加SystemConfiguration记录
2. 或在init_system命令中添加默认配置

### 自定义权限控制
继承UserPassesTestMixin并实现test_func方法：

```python
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务是否启动
   - 验证数据库连接参数

2. **Redis连接失败**
   - 检查Redis服务是否启动
   - 验证Redis连接参数

3. **静态文件404**
   - 运行 `python manage.py collectstatic`
   - 检查STATIC_ROOT配置

4. **权限错误**
   - 检查用户角色设置
   - 验证权限装饰器

### 日志查看
Django日志文件位置：`logs/django.log`

### 性能优化
- 启用Redis缓存
- 使用数据库索引
- 优化查询语句
- 启用Gzip压缩

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

本项目采用MIT许可证。