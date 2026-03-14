"""
数据模型定义

定义系统的数据结构和数据库模型，支持PostgreSQL数据库。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json


class SystemStatus(Enum):
    """系统状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class SystemConfig:
    """系统配置数据模型"""
    # 检测相关配置
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    detection_fps: int = 15
    
    # 风险监控配置
    stove_distance_threshold: float = 2.0  # 米
    unattended_time_threshold: int = 300   # 秒
    fall_confidence_threshold: float = 0.8
    
    # 报警配置
    alert_cooldown_time: int = 30  # 秒
    enable_sound_alert: bool = True
    enable_email_alert: bool = True
    enable_sms_alert: bool = False
    
    # 视频配置
    video_input_source: str = "0"  # 摄像头ID或视频文件路径
    video_resolution: tuple = (640, 480)
    video_fps: int = 30
    
    # 性能配置
    max_cpu_usage: float = 80.0
    max_memory_usage: float = 70.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'confidence_threshold': self.confidence_threshold,
            'nms_threshold': self.nms_threshold,
            'detection_fps': self.detection_fps,
            'stove_distance_threshold': self.stove_distance_threshold,
            'unattended_time_threshold': self.unattended_time_threshold,
            'fall_confidence_threshold': self.fall_confidence_threshold,
            'alert_cooldown_time': self.alert_cooldown_time,
            'enable_sound_alert': self.enable_sound_alert,
            'enable_email_alert': self.enable_email_alert,
            'enable_sms_alert': self.enable_sms_alert,
            'video_input_source': self.video_input_source,
            'video_resolution': list(self.video_resolution),
            'video_fps': self.video_fps,
            'max_cpu_usage': self.max_cpu_usage,
            'max_memory_usage': self.max_memory_usage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """从字典创建配置对象"""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                if key == 'video_resolution' and isinstance(value, list):
                    setattr(config, key, tuple(value))
                else:
                    setattr(config, key, value)
        return config


@dataclass
class DetectionResult:
    """检测结果数据模型"""
    frame_id: str = ""
    timestamp: Optional[datetime] = None
    detections: List[Dict[str, Any]] = field(default_factory=list)
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'frame_id': self.frame_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'detections': self.detections,
            'processing_time': self.processing_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectionResult':
        """从字典创建检测结果对象"""
        return cls(
            frame_id=data.get('frame_id', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            detections=data.get('detections', []),
            processing_time=data.get('processing_time', 0.0)
        )


@dataclass
class DetectionStats:
    """检测统计数据"""
    total_frames_processed: int = 0
    total_detections: int = 0
    person_detections: int = 0
    stove_detections: int = 0
    flame_detections: int = 0
    fall_events: int = 0
    unattended_stove_events: int = 0
    average_fps: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_update_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_frames_processed': self.total_frames_processed,
            'total_detections': self.total_detections,
            'person_detections': self.person_detections,
            'stove_detections': self.stove_detections,
            'flame_detections': self.flame_detections,
            'fall_events': self.fall_events,
            'unattended_stove_events': self.unattended_stove_events,
            'average_fps': self.average_fps,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None
        }


@dataclass
class AlertRecord:
    """报警记录数据模型"""
    id: Optional[str] = None
    alert_type: str = ""
    alert_level: str = ""
    timestamp: Optional[datetime] = None
    location_x: Optional[int] = None
    location_y: Optional[int] = None
    description: str = ""
    video_clip_path: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'alert_level': self.alert_level,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'location_x': self.location_x,
            'location_y': self.location_y,
            'description': self.description,
            'video_clip_path': self.video_clip_path,
            'additional_data': json.dumps(self.additional_data) if self.additional_data else None,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertRecord':
        """从字典创建记录对象"""
        return cls(
            id=data.get('id'),
            alert_type=data.get('alert_type', ''),
            alert_level=data.get('alert_level', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            location_x=data.get('location_x'),
            location_y=data.get('location_y'),
            description=data.get('description', ''),
            video_clip_path=data.get('video_clip_path'),
            additional_data=json.loads(data['additional_data']) if data.get('additional_data') else None,
            resolved=data.get('resolved', False),
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None,
            resolved_by=data.get('resolved_by')
        )


@dataclass
class LogRecord:
    """日志记录数据模型"""
    id: Optional[str] = None
    level: str = "INFO"
    message: str = ""
    timestamp: Optional[datetime] = None
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'module': self.module,
            'function': self.function,
            'line_number': self.line_number,
            'additional_data': json.dumps(self.additional_data) if self.additional_data else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogRecord':
        """从字典创建记录对象"""
        return cls(
            id=data.get('id'),
            level=data.get('level', 'INFO'),
            message=data.get('message', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            module=data.get('module'),
            function=data.get('function'),
            line_number=data.get('line_number'),
            additional_data=json.loads(data['additional_data']) if data.get('additional_data') else None
        )


@dataclass
class UserProfile:
    """用户配置数据模型"""
    id: Optional[str] = None
    username: str = ""
    email: str = ""
    role: str = "user"  # admin, user
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    notification_preferences: Dict[str, bool] = field(default_factory=lambda: {
        'email_alerts': True,
        'sms_alerts': False,
        'sound_alerts': True
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'notification_preferences': json.dumps(self.notification_preferences)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """从字典创建用户对象"""
        return cls(
            id=data.get('id'),
            username=data.get('username', ''),
            email=data.get('email', ''),
            role=data.get('role', 'user'),
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            notification_preferences=json.loads(data['notification_preferences']) if data.get('notification_preferences') else {
                'email_alerts': True,
                'sms_alerts': False,
                'sound_alerts': True
            }
        )


# 数据库表结构定义 (用于PostgreSQL)
DATABASE_SCHEMA = {
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            notification_preferences JSONB DEFAULT '{"email_alerts": true, "sms_alerts": false, "sound_alerts": true}'
        );
    ''',
    
    'alert_records': '''
        CREATE TABLE IF NOT EXISTS alert_records (
            id SERIAL PRIMARY KEY,
            alert_type VARCHAR(50) NOT NULL,
            alert_level VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            location_x INTEGER,
            location_y INTEGER,
            description TEXT,
            video_clip_path VARCHAR(500),
            additional_data JSONB,
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMP,
            resolved_by VARCHAR(50)
        );
    ''',
    
    'log_records': '''
        CREATE TABLE IF NOT EXISTS log_records (
            id SERIAL PRIMARY KEY,
            level VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            module VARCHAR(100),
            function VARCHAR(100),
            line_number INTEGER,
            additional_data JSONB
        );
    ''',
    
    'system_configs': '''
        CREATE TABLE IF NOT EXISTS system_configs (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR(100) UNIQUE NOT NULL,
            config_value JSONB NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by VARCHAR(50)
        );
    ''',
    
    'detection_stats': '''
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
    '''
}

# 数据库索引定义
DATABASE_INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_alert_records_timestamp ON alert_records(timestamp);',
    'CREATE INDEX IF NOT EXISTS idx_alert_records_type ON alert_records(alert_type);',
    'CREATE INDEX IF NOT EXISTS idx_log_records_timestamp ON log_records(timestamp);',
    'CREATE INDEX IF NOT EXISTS idx_log_records_level ON log_records(level);',
    'CREATE INDEX IF NOT EXISTS idx_detection_stats_timestamp ON detection_stats(timestamp);'
]