# 厨房安全检测系统 - 快速开始指南

## 🚀 5分钟快速部署

### 前提条件

确保您的系统已安装：
- Docker (20.10+)
- Docker Compose (1.29+)

### 快速部署步骤

#### 1. 获取代码
```bash
# 如果使用Git
git clone <repository-url>
cd kitchen-safety-detection-system

# 或者解压代码包到目录
```

#### 2. 配置环境
```bash
# 复制环境配置
cp .env.example .env

# 快速配置 (最小化配置)
sed -i 's/your-very-secure-secret-key-change-in-production-environment/kitchen-safety-secret-2024/g' .env
sed -i 's/kitchen_pass_secure_2024/kitchen_pass_2024/g' .env
```

#### 3. 一键部署
```bash
# 给脚本执行权限
chmod +x scripts/deploy.sh

# 执行部署
./scripts/deploy.sh
```

#### 4. 访问系统
部署完成后，打开浏览器访问：
- **主界面**: http://localhost
- **管理后台**: http://localhost/admin/

默认登录信息：
- 用户名: `admin`
- 密码: `admin123`

## 🎯 核心功能验证

### 1. 系统状态检查
```bash
# 检查所有服务状态
./scripts/maintenance.sh health-check
```

### 2. 演示模式测试
```bash
# 进入容器运行演示
docker-compose exec kitchen_safety python demo.py
```

### 3. API测试
```bash
# 健康检查
curl http://localhost/health

# 系统状态
curl http://localhost/api/status/
```

## 📊 监控面板

访问 http://localhost 查看：
- 实时检测状态
- 报警历史记录
- 系统性能监控
- 配置管理界面

## 🔧 常用命令

### 服务管理
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f kitchen_safety

# 重启服务
docker-compose restart kitchen_safety

# 停止所有服务
docker-compose down
```

### 维护操作
```bash
# 备份数据
./scripts/maintenance.sh backup

# 清理日志
./scripts/maintenance.sh cleanup-logs

# 系统健康检查
./scripts/maintenance.sh health-check
```

## 🛠️ 自定义配置

### 检测参数调整
编辑 `.env` 文件：
```bash
# 检测帧率 (降低可减少CPU使用)
KITCHEN_SAFETY_DETECTION_FPS=15

# 置信度阈值 (提高可减少误检)
KITCHEN_SAFETY_CONFIDENCE_THRESHOLD=0.5

# 无人看管时间阈值 (秒)
KITCHEN_SAFETY_UNATTENDED_TIME=300
```

### 报警配置
```bash
# 启用邮件报警
KITCHEN_SAFETY_ENABLE_EMAIL=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# 启用声音报警
KITCHEN_SAFETY_ENABLE_SOUND=true
```

## 🚨 故障排除

### 常见问题

#### 端口被占用
```bash
# 检查端口占用
netstat -tulpn | grep :80

# 修改端口 (编辑 docker-compose.yml)
ports:
  - "8080:80"  # 改为8080端口
```

#### 内存不足
```bash
# 检查内存使用
free -h

# 降低资源使用 (编辑 .env)
KITCHEN_SAFETY_DETECTION_FPS=10
```

#### 服务启动失败
```bash
# 查看详细日志
docker-compose logs [service_name]

# 重新构建镜像
docker-compose build --no-cache
docker-compose up -d
```

### 获取帮助
```bash
# 查看部署脚本帮助
./scripts/deploy.sh --help

# 查看维护脚本帮助
./scripts/maintenance.sh help
```

## 📝 下一步

1. **安全配置**: 修改默认密码和密钥
2. **性能调优**: 根据硬件配置调整参数
3. **监控设置**: 配置日志监控和报警
4. **备份策略**: 设置定期数据备份

详细配置请参考 [完整部署文档](DEPLOYMENT.md)。

---

🎉 **恭喜！** 您已成功部署厨房安全检测系统！