-- 厨房安全检测系统数据库初始化脚本

-- 创建数据库 (如果不存在)
-- CREATE DATABASE kitchen_safety;

-- 连接到数据库
\c kitchen_safety;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'operator')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    notification_preferences JSONB DEFAULT '{"email_alerts": true, "sms_alerts": false, "sound_alerts": true}',
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_username CHECK (length(username) >= 3)
);

-- 创建报警记录表
CREATE TABLE IF NOT EXISTS alert_records (
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
    resolved_by VARCHAR(50),
    CONSTRAINT resolved_consistency CHECK (
        (resolved = FALSE AND resolved_at IS NULL AND resolved_by IS NULL) OR
        (resolved = TRUE AND resolved_at IS NOT NULL AND resolved_by IS NOT NULL)
    )
);

-- 创建日志记录表
CREATE TABLE IF NOT EXISTS log_records (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    module VARCHAR(100),
    function VARCHAR(100),
    line_number INTEGER CHECK (line_number > 0),
    additional_data JSONB
);

-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

-- 创建检测统计表
CREATE TABLE IF NOT EXISTS detection_stats (
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

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_alert_records_timestamp ON alert_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_alert_records_type ON alert_records(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_records_level ON alert_records(alert_level);
CREATE INDEX IF NOT EXISTS idx_alert_records_resolved ON alert_records(resolved);
CREATE INDEX IF NOT EXISTS idx_alert_records_type_timestamp ON alert_records(alert_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_log_records_timestamp ON log_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_records_level ON log_records(level);
CREATE INDEX IF NOT EXISTS idx_log_records_module ON log_records(module);
CREATE INDEX IF NOT EXISTS idx_log_records_level_timestamp ON log_records(level, timestamp);
CREATE INDEX IF NOT EXISTS idx_detection_stats_timestamp ON detection_stats(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_configs_key ON system_configs(config_key);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 插入默认管理员用户 (密码: admin123)
INSERT INTO users (username, email, password_hash, role) 
VALUES ('admin', 'admin@kitchensafety.com', 'pbkdf2_sha256$320000$default$hash', 'admin')
ON CONFLICT (username) DO NOTHING;

-- 插入默认系统配置
INSERT INTO system_configs (config_key, config_value, updated_by) VALUES
('detection_settings', '{"confidence_threshold": 0.5, "nms_threshold": 0.4, "detection_fps": 15}', 'system'),
('risk_monitoring', '{"stove_distance_threshold": 2.0, "unattended_time_threshold": 300, "fall_confidence_threshold": 0.8}', 'system'),
('alert_settings', '{"alert_cooldown_time": 30, "enable_sound_alert": true, "enable_email_alert": true, "enable_sms_alert": false}', 'system'),
('video_settings', '{"input_source": "0", "resolution": [640, 480], "fps": 30}', 'system'),
('performance_settings', '{"max_cpu_usage": 80.0, "max_memory_usage": 70.0}', 'system')
ON CONFLICT (config_key) DO NOTHING;

-- 创建视图：最新检测统计
CREATE OR REPLACE VIEW latest_detection_stats AS
SELECT * FROM detection_stats 
WHERE timestamp = (SELECT MAX(timestamp) FROM detection_stats);

-- 创建视图：未解决的报警
CREATE OR REPLACE VIEW unresolved_alerts AS
SELECT * FROM alert_records 
WHERE resolved = FALSE 
ORDER BY timestamp DESC;

-- 创建视图：今日统计
CREATE OR REPLACE VIEW today_stats AS
SELECT 
    COUNT(*) as total_alerts,
    COUNT(CASE WHEN alert_type = 'fall_detected' THEN 1 END) as fall_alerts,
    COUNT(CASE WHEN alert_type = 'unattended_stove' THEN 1 END) as stove_alerts,
    COUNT(CASE WHEN resolved = TRUE THEN 1 END) as resolved_alerts
FROM alert_records 
WHERE DATE(timestamp) = CURRENT_DATE;

-- 授予权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kitchen_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kitchen_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO kitchen_user;