"""
核心模块

提供系统的核心接口、数据模型和配置管理。
"""

from .interfaces import *
from .models import *
from .config import config_manager, get_config, set_config

__all__ = [
    # 接口类
    'IVideoCapture',
    'IVideoProcessor', 
    'IObjectDetector',
    'IPoseAnalyzer',
    'IRiskMonitor',
    'IAlertManager',
    'IConfigurationManager',
    'ILogSystem',
    'IDetectionSystem',
    
    # 数据结构
    'DetectionType',
    'AlertType',
    'AlertLevel',
    'BoundingBox',
    'DetectionResult',
    'PoseKeypoint',
    'PoseResult',
    'AlertEvent',
    
    # 数据模型
    'SystemStatus',
    'SystemConfig',
    'DetectionStats',
    'AlertRecord',
    'LogRecord',
    'UserProfile',
    
    # 配置管理
    'config_manager',
    'get_config',
    'set_config'
]