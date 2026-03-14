# 厨房安全检测系统 - 数据库和缓存系统

## 概述

本系统使用PostgreSQL作为主数据库，Redis作为缓存系统，为厨房安全检测系统提供可靠的数据存储和高性能的数据访问。

## 架构设计

### 数据库层次结构

```
数据库和缓存系统
├── PostgreSQL 数据库
│   ├── 用户管理 (users)
│   ├── 报警记录 (alert_records)
│   ├── 日志记录 (log_records)
│   ├── 系统配置 (system_configs)
│   └── 检测统计 (detection_stats)
├── Redis 缓存
│   ├── 检测结果缓存
│   ├── 系统配置缓存
│   ├── 统计数据缓存
│   ├── 报警数据缓存
│   └── 实时数据流
└── 数据访问层
    ├── 数据库连接管理
    ├── 缓存管理器
    ├── 数据仓库模式
    └── CLI管理工具
```

## 数据库设计

### 核心数据表

#### 1. 用户表 (users)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'operator')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    notification_preferences JSONB DEFAULT '{"email_alerts": true, "sms_alerts": false, "sound_alerts": true}'
);
```

#### 2. 报警记录表 (alert_records)
```sql
CREATE TABLE alert_records (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('fall_detected', 'unattended_stove', 'system_error', 'performance_warning')),
    alert_level VARCHAR(20) NOT NULL CHECK (alert_level IN ('low', 'medium', 'high', 'critical')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location_x INTEGER CHECK (location_x >= 0),
    location_y INTEGER CHECK (location_y >= 0),
    description TEXT,
    video_clip_path VARCHAR(500),
    additional_data JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(50)
);
```

#### 3. 日志记录表 (log_records)
```sql
CREATE TABLE log_records (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    module VARCHAR(100),
    function VARCHAR(100),
    line_number INTEGER CHECK (line_number > 0),
    additional_data JSONB
);
```

#### 4. 系统配置表 (system_configs)
```sql
CREATE TABLE system_configs (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);
```

#### 5. 检测统计表 (detection_stats)
```sql
CREATE TABLE detection_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_frames_processed INTEGER DEFAULT 0,
    total_detections INTEGER DEFAULT 0,
    person_detections INTEGER DEFAULT 0,
    stove_detections INTEGER DEFAULT 0,
    flame_detections INTEGER DEFAULT 0,
    fall_events INTEGER DEFAULT 0,
    unattended_stove_events INTEGER DEFAULT 0,
    average_fps FLOAT DEFAULT 0.0,
    cpu_usage FLOAT DEFAULT 0.0,
    memory_usage FLOAT DEFAULT 0.0
);
```

### 索引优化

系统创建了以下索引以优化查询性能：

```sql
-- 报警记录索引
CREATE INDEX idx_alert_records_timestamp ON alert_records(timestamp);
CREATE INDEX idx_alert_records_type ON alert_records(alert_type);
CREATE INDEX idx_alert_records_level ON alert_records(alert_level);
CREATE INDEX idx_alert_records_resolved ON alert_records(resolved);
CREATE INDEX idx_alert_records_type_timestamp ON alert_records(alert_type, timestamp);

-- 日志记录索引
CREATE INDEX idx_log_records_timestamp ON log_records(timestamp);
CREATE INDEX idx_log_records_level ON log_records(level);
CREATE INDEX idx_log_records_module ON log_records(module);
CREATE INDEX idx_log_records_level_timestamp ON log_records(level, timestamp);

-- 其他索引
CREATE INDEX idx_detection_stats_timestamp ON detection_stats(timestamp);
CREATE INDEX idx_system_configs_key ON system_configs(config_key);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

## 缓存系统设计

### Redis 缓存策略

#### 1. 检测结果缓存
- **键格式**: `kitchen_safety:detection:frame:{frame_id}`
- **TTL**: 300秒 (5分钟)
- **用途**: 缓存实时检测结果，避免重复计算

#### 2. 系统配置缓存
- **键格式**: `kitchen_safety:config:{config_key}`
- **TTL**: 3600秒 (1小时)
- **用途**: 缓存系统配置，减少数据库访问

#### 3. 统计数据缓存
- **键格式**: `kitchen_safety:stats:{stats_type}`
- **TTL**: 60秒 (1分钟)
- **用途**: 缓存统计数据，提高仪表板响应速度

#### 4. 报警数据缓存
- **键格式**: `kitchen_safety:alert:{alert_type}`
- **TTL**: 1800秒 (30分钟)
- **用途**: 缓存最近的报警记录

#### 5. 实时数据流
- **键格式**: `kitchen_safety:realtime:{data_type}`
- **数据结构**: Redis List
- **用途**: 存储实时检测数据流

### 缓存失效策略

1. **主动失效**: 数据更新时主动清除相关缓存
2. **TTL失效**: 设置合理的过期时间
3. **LRU淘汰**: Redis内存不足时自动淘汰

## 使用指南

### 1. 环境配置

创建 `.env` 文件：
```bash
# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=kitchen_safety
DATABASE_USER=kitchen_user
DATABASE_PASSWORD=kitchen_pass

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### 2. 数据库初始化

使用Docker Compose启动服务：
```bash
docker-compose up -d postgres redis
```

运行数据库初始化脚本：
```bash
python database/setup_database.py
```

### 3. 代码使用示例

#### 数据库操作
```python
from kitchen_safety_system.database import alert_repo, config_repo
from kitchen_safety_system.core.models import AlertRecord

# 创建报警记录
alert = AlertRecord(
    alert_type="fall_detected",
    alert_level="high",
    description="检测到人员跌倒"
)
alert_id = alert_repo.create(alert)

# 获取系统配置
config = config_repo.get("detection_settings")
```

#### 缓存操作
```python
from kitchen_safety_system.database import get_cache_manager

cache = get_cache_manager()

# 缓存检测结果
detection_result = DetectionResult(...)
cache.cache_detection_result("frame_001", detection_result)

# 获取缓存的配置
config = cache.get_system_config("detection_settings")
```

### 4. CLI管理工具

查看数据库状态：
```bash
python kitchen_safety_system/database/cli.py db status
```

查看缓存信息：
```bash
python kitchen_safety_system/database/cli.py cache info
```

查看报警记录：
```bash
python kitchen_safety_system/database/cli.py db alerts --limit 10
```

管理系统配置：
```bash
# 查看所有配置
python kitchen_safety_system/database/cli.py config list

# 设置配置
python kitchen_safety_system/database/cli.py config set detection_settings '{"confidence_threshold": 0.6}'

# 获取配置
python kitchen_safety_system/database/cli.py config get detection_settings
```

## 性能优化

### 1. 数据库优化

- **连接池**: 使用连接池管理数据库连接
- **索引优化**: 为常用查询字段创建索引
- **分区表**: 对大表进行时间分区
- **定期维护**: 定期清理过期数据

### 2. 缓存优化

- **缓存预热**: 系统启动时预加载常用数据
- **批量操作**: 使用Pipeline进行批量缓存操作
- **内存监控**: 监控Redis内存使用情况
- **数据压缩**: 对大数据进行压缩存储

### 3. 监控指标

- **数据库连接数**: 监控活跃连接数
- **查询响应时间**: 监控慢查询
- **缓存命中率**: 监控缓存效果
- **内存使用率**: 监控Redis内存使用

## 备份和恢复

### 1. 数据库备份

```bash
# 自动备份
python kitchen_safety_system/database/cli.py backup

# 手动备份
pg_dump -h localhost -U kitchen_user -d kitchen_safety -f backup.sql
```

### 2. Redis备份

```bash
# Redis持久化配置
redis-cli BGSAVE
```

### 3. 恢复数据

```bash
# 恢复PostgreSQL
psql -h localhost -U kitchen_user -d kitchen_safety -f backup.sql

# 恢复Redis
redis-cli --rdb dump.rdb
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接参数
   - 检查网络连接

2. **Redis连接失败**
   - 检查Redis服务状态
   - 验证Redis配置
   - 检查防火墙设置

3. **缓存命中率低**
   - 检查TTL设置
   - 优化缓存策略
   - 增加缓存容量

4. **数据库性能问题**
   - 分析慢查询日志
   - 优化索引设计
   - 考虑读写分离

### 日志分析

```bash
# 查看错误日志
python kitchen_safety_system/database/cli.py db logs --level ERROR

# 查看性能统计
python kitchen_safety_system/database/cli.py db stats --days 7
```

## 安全考虑

### 1. 数据库安全

- **访问控制**: 使用专用数据库用户
- **网络隔离**: 限制数据库网络访问
- **数据加密**: 敏感数据加密存储
- **审计日志**: 记录数据库操作日志

### 2. 缓存安全

- **访问认证**: 配置Redis密码
- **网络安全**: 使用防火墙限制访问
- **数据过期**: 设置合理的TTL
- **敏感数据**: 避免缓存敏感信息

## 扩展性考虑

### 1. 水平扩展

- **读写分离**: 主从复制分离读写
- **分片策略**: 按时间或业务分片
- **负载均衡**: 使用连接池和负载均衡

### 2. 垂直扩展

- **硬件升级**: 增加CPU、内存、存储
- **参数调优**: 优化数据库参数
- **索引优化**: 持续优化索引设计

## 维护计划

### 日常维护

- **监控检查**: 每日检查系统状态
- **性能分析**: 每周分析性能指标
- **数据清理**: 每月清理过期数据
- **备份验证**: 每月验证备份完整性

### 定期维护

- **索引重建**: 每季度重建索引
- **统计更新**: 每季度更新表统计信息
- **容量规划**: 每半年进行容量规划
- **安全审计**: 每年进行安全审计