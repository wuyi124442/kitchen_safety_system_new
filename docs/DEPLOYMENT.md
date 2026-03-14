# 厨房安全检测系统 - 容器化部署文档

## 概述

本文档详细介绍了厨房安全检测系统的容器化部署方案，包括Docker配置、部署流程、维护管理等内容。

## 系统架构

### 容器架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │  Kitchen Safety │    │   Django Web    │
│   (反向代理)     │◄──►│   (主检测服务)   │◄──►│   (管理界面)     │
│   Port: 80/443  │    │   Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    │    ┌─────────────────┐
         │   PostgreSQL    │◄───┼───►│     Redis       │
         │   (数据库)       │    │    │    (缓存)       │
         │   Port: 5432    │    │    │   Port: 6379    │
         └─────────────────┘    │    └─────────────────┘
                                │
                    ┌─────────────────┐
                    │   File System   │
                    │  (日志/配置/模型) │
                    └─────────────────┘
```

### 服务组件

| 服务名称 | 镜像 | 端口 | 功能描述 |
|---------|------|------|----------|
| nginx | nginx:alpine | 80, 443 | 反向代理和负载均衡 |
| kitchen_safety | 自构建 | 8000 | 主检测服务 |
| web | 自构建 | 8001 | Django管理界面 |
| postgres | postgres:14-alpine | 5432 | 数据库服务 |
| redis | redis:7-alpine | 6379 | 缓存服务 |

## 系统要求

### 硬件要求

- **CPU**: 最低2核，推荐4核以上
- **内存**: 最低4GB，推荐8GB以上
- **存储**: 最低20GB可用空间，推荐50GB以上
- **网络**: 稳定的网络连接

### 软件要求

- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+) 或 macOS
- **Docker**: 版本 20.10+
- **Docker Compose**: 版本 1.29+
- **Git**: 用于代码管理 (可选)

### 端口要求

确保以下端口未被占用：
- 80 (HTTP)
- 443 (HTTPS)
- 5432 (PostgreSQL)
- 6379 (Redis)
- 8000 (主应用)
- 8001 (Web管理)

## 快速部署

### 1. 获取代码

```bash
# 克隆仓库 (如果使用Git)
git clone <repository-url>
cd kitchen-safety-detection-system

# 或者直接解压代码包
```

### 2. 配置环境

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

**重要配置项**：
```bash
# 数据库密码 (必须修改)
POSTGRES_PASSWORD=your_secure_password

# Django密钥 (必须修改)
DJANGO_SECRET_KEY=your_very_secure_secret_key

# 允许的主机 (根据实际域名修改)
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# 邮件配置 (如果启用邮件报警)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. 执行部署

```bash
# 给脚本执行权限
chmod +x scripts/deploy.sh scripts/maintenance.sh

# 执行部署
./scripts/deploy.sh
```

### 4. 验证部署

部署完成后，访问以下地址验证：

- **Web管理界面**: http://localhost
- **API健康检查**: http://localhost/health
- **Django管理**: http://localhost/admin/

默认管理员账户：
- 用户名: `admin`
- 密码: `admin123` (请及时修改)

## 详细配置

### Docker配置

#### Dockerfile 特性

- **多阶段构建**: 优化镜像大小
- **非root用户**: 提高安全性
- **健康检查**: 自动监控服务状态
- **启动脚本**: 智能初始化和错误处理

#### docker-compose.yml 特性

- **服务依赖**: 确保启动顺序
- **健康检查**: 监控服务状态
- **资源限制**: 防止资源滥用
- **数据持久化**: 重要数据不丢失
- **网络隔离**: 提高安全性

### 环境变量配置

#### 数据库配置
```bash
POSTGRES_PASSWORD=secure_password
DATABASE_HOST=postgres
DATABASE_NAME=kitchen_safety
DATABASE_USER=kitchen_user
```

#### 应用配置
```bash
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=localhost,your-domain.com
LOG_LEVEL=INFO
```

#### 检测配置
```bash
KITCHEN_SAFETY_CONFIDENCE_THRESHOLD=0.5
KITCHEN_SAFETY_DETECTION_FPS=15
KITCHEN_SAFETY_STOVE_DISTANCE=2.0
KITCHEN_SAFETY_UNATTENDED_TIME=300
```

### 网络配置

#### Nginx配置

Nginx作为反向代理，提供以下功能：

- **负载均衡**: 分发请求到后端服务
- **静态文件服务**: 高效处理静态资源
- **SSL终止**: HTTPS支持 (需要配置证书)
- **请求缓存**: 提高响应速度
- **安全头**: 增强安全性

#### 端口映射

```yaml
services:
  nginx:
    ports:
      - "80:80"      # HTTP
      - "443:443"    # HTTPS
  kitchen_safety:
    ports:
      - "8000:8000"  # 主应用 (可选暴露)
  web:
    ports:
      - "8001:8001"  # Web管理 (可选暴露)
```

## 部署脚本详解

### deploy.sh 脚本

主要功能：
- **环境检查**: 验证Docker和系统要求
- **配置验证**: 检查关键配置项
- **镜像构建**: 构建应用镜像
- **服务启动**: 按顺序启动所有服务
- **健康检查**: 验证部署结果

使用方法：
```bash
./scripts/deploy.sh           # 完整部署
./scripts/deploy.sh --update  # 更新部署
./scripts/deploy.sh --status  # 检查状态
./scripts/deploy.sh --cleanup # 清理部署
```

### maintenance.sh 脚本

主要功能：
- **数据备份**: 自动备份数据库
- **日志清理**: 清理过期日志文件
- **健康检查**: 监控系统状态
- **服务管理**: 重启和管理服务

使用方法：
```bash
./scripts/maintenance.sh backup           # 备份数据库
./scripts/maintenance.sh health-check     # 健康检查
./scripts/maintenance.sh cleanup-logs 7   # 清理7天前日志
./scripts/maintenance.sh restart web      # 重启Web服务
```

## 生产环境部署

### 安全配置

#### 1. 修改默认密码
```bash
# 数据库密码
POSTGRES_PASSWORD=complex_secure_password_2024

# Django密钥 (使用随机生成)
DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
```

#### 2. 启用HTTPS
```bash
# 生成SSL证书 (自签名示例)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/nginx-selfsigned.key \
  -out nginx/ssl/nginx-selfsigned.crt

# 更新nginx配置启用HTTPS
```

#### 3. 防火墙配置
```bash
# Ubuntu/Debian
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 5432/tcp  # 禁止外部访问数据库
ufw deny 6379/tcp  # 禁止外部访问Redis

# CentOS/RHEL
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload
```

### 性能优化

#### 1. 资源限制
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

#### 2. 数据库优化
```bash
# PostgreSQL配置优化
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

#### 3. Redis优化
```bash
# Redis配置
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

### 监控配置

#### 1. 日志监控
```bash
# 配置日志轮转
/etc/logrotate.d/kitchen-safety
```

#### 2. 健康检查
```bash
# 定时健康检查
*/5 * * * * /path/to/scripts/maintenance.sh health-check
```

#### 3. 备份策略
```bash
# 每日数据库备份
0 2 * * * /path/to/scripts/maintenance.sh backup
# 每周清理旧备份
0 3 * * 0 /path/to/scripts/maintenance.sh cleanup-backups 30
```

## 故障排除

### 常见问题

#### 1. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep :80
lsof -i :80

# 解决方案：修改docker-compose.yml中的端口映射
```

#### 2. 内存不足
```bash
# 检查内存使用
free -h
docker stats

# 解决方案：增加系统内存或调整资源限制
```

#### 3. 数据库连接失败
```bash
# 检查数据库状态
docker-compose logs postgres

# 检查网络连接
docker-compose exec kitchen_safety ping postgres
```

#### 4. 权限问题
```bash
# 检查文件权限
ls -la logs/ data/

# 修复权限
sudo chown -R $USER:$USER logs/ data/
chmod -R 755 logs/ data/
```

### 调试命令

```bash
# 查看所有容器状态
docker-compose ps

# 查看服务日志
docker-compose logs -f [service_name]

# 进入容器调试
docker-compose exec [service_name] bash

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose restart [service_name]

# 完全重新部署
docker-compose down -v
docker-compose up -d
```

### 性能调优

#### 1. 检测性能优化
```bash
# 调整检测帧率
KITCHEN_SAFETY_DETECTION_FPS=10  # 降低帧率减少CPU使用

# 调整置信度阈值
KITCHEN_SAFETY_CONFIDENCE_THRESHOLD=0.6  # 提高阈值减少误检
```

#### 2. 数据库性能优化
```sql
-- 创建索引
CREATE INDEX idx_alerts_timestamp ON alerts(created_at);
CREATE INDEX idx_logs_level ON logs(level);

-- 定期清理数据
DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days';
```

#### 3. 缓存优化
```bash
# Redis内存优化
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory 256mb
```

## 升级和维护

### 版本升级

```bash
# 1. 备份数据
./scripts/maintenance.sh backup

# 2. 拉取新版本
git pull origin main

# 3. 更新部署
./scripts/deploy.sh --update

# 4. 验证升级
./scripts/maintenance.sh health-check
```

### 定期维护

```bash
# 每日任务
./scripts/maintenance.sh backup
./scripts/maintenance.sh health-check

# 每周任务
./scripts/maintenance.sh cleanup-logs 7
docker system prune -f

# 每月任务
./scripts/maintenance.sh cleanup-backups 30
```

### 数据迁移

```bash
# 导出数据
./scripts/maintenance.sh backup

# 在新环境导入
./scripts/maintenance.sh restore backup_file.sql.gz
```

## 安全最佳实践

### 1. 网络安全
- 使用防火墙限制端口访问
- 启用HTTPS加密传输
- 定期更新SSL证书

### 2. 数据安全
- 定期备份重要数据
- 加密敏感配置信息
- 限制数据库访问权限

### 3. 应用安全
- 定期更新依赖包
- 使用强密码策略
- 启用访问日志记录

### 4. 容器安全
- 使用非root用户运行
- 定期更新基础镜像
- 扫描镜像安全漏洞

## 支持和联系

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查系统日志和容器日志
3. 联系技术支持团队

---

**注意**: 本文档会随着系统更新而持续更新，请定期查看最新版本。