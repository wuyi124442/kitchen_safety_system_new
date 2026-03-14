"""
核心模块测试

测试核心接口和数据模型的基本功能。
"""

import pytest
from datetime import datetime
from kitchen_safety_system.core.models import (
    SystemConfig, DetectionStats, AlertRecord, LogRecord, UserProfile
)
from kitchen_safety_system.core.interfaces import (
    DetectionType, AlertType, AlertLevel, BoundingBox, DetectionResult, 
    PoseKeypoint, PoseResult, AlertEvent
)
from kitchen_safety_system.core.config import ConfigManager


class TestDataModels:
    """测试数据模型"""
    
    def test_system_config_creation(self):
        """测试系统配置创建"""
        config = SystemConfig()
        assert config.confidence_threshold == 0.5
        assert config.detection_fps == 15
        assert config.enable_sound_alert is True
    
    def test_system_config_to_dict(self):
        """测试系统配置转换为字典"""
        config = SystemConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'confidence_threshold' in config_dict
        assert 'detection_fps' in config_dict
        assert config_dict['confidence_threshold'] == 0.5
    
    def test_system_config_from_dict(self):
        """测试从字典创建系统配置"""
        data = {
            'confidence_threshold': 0.7,
            'detection_fps': 20,
            'enable_sound_alert': False
        }
        config = SystemConfig.from_dict(data)
        
        assert config.confidence_threshold == 0.7
        assert config.detection_fps == 20
        assert config.enable_sound_alert is False
    
    def test_detection_stats_creation(self):
        """测试检测统计数据创建"""
        stats = DetectionStats()
        assert stats.total_frames_processed == 0
        assert stats.total_detections == 0
        assert stats.average_fps == 0.0
    
    def test_alert_record_creation(self):
        """测试报警记录创建"""
        record = AlertRecord(
            alert_type="fall_detected",
            alert_level="high",
            description="检测到人员跌倒"
        )
        assert record.alert_type == "fall_detected"
        assert record.alert_level == "high"
        assert record.resolved is False
    
    def test_log_record_creation(self):
        """测试日志记录创建"""
        record = LogRecord(
            level="INFO",
            message="系统启动成功"
        )
        assert record.level == "INFO"
        assert record.message == "系统启动成功"
    
    def test_user_profile_creation(self):
        """测试用户配置创建"""
        user = UserProfile(
            username="testuser",
            email="test@example.com",
            role="admin"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "admin"
        assert user.is_active is True


class TestInterfaces:
    """测试接口定义"""
    
    def test_detection_type_enum(self):
        """测试检测类型枚举"""
        assert DetectionType.PERSON.value == "person"
        assert DetectionType.STOVE.value == "stove"
        assert DetectionType.FLAME.value == "flame"
    
    def test_alert_type_enum(self):
        """测试报警类型枚举"""
        assert AlertType.FALL_DETECTED.value == "fall_detected"
        assert AlertType.UNATTENDED_STOVE.value == "unattended_stove"
        assert AlertType.SYSTEM_ERROR.value == "system_error"
    
    def test_alert_level_enum(self):
        """测试报警级别枚举"""
        assert AlertLevel.LOW.value == "low"
        assert AlertLevel.MEDIUM.value == "medium"
        assert AlertLevel.HIGH.value == "high"
        assert AlertLevel.CRITICAL.value == "critical"
    
    def test_bounding_box_creation(self):
        """测试边界框创建"""
        bbox = BoundingBox(x=10, y=20, width=100, height=200, confidence=0.8)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 200
        assert bbox.confidence == 0.8
    
    def test_bounding_box_center(self):
        """测试边界框中心点计算"""
        bbox = BoundingBox(x=10, y=20, width=100, height=200, confidence=0.8)
        center = bbox.center
        assert center == (60, 120)  # (10 + 100//2, 20 + 200//2)
    
    def test_bounding_box_area(self):
        """测试边界框面积计算"""
        bbox = BoundingBox(x=10, y=20, width=100, height=200, confidence=0.8)
        area = bbox.area
        assert area == 20000  # 100 * 200
    
    def test_detection_result_creation(self):
        """测试检测结果创建"""
        bbox = BoundingBox(x=10, y=20, width=100, height=200, confidence=0.8)
        result = DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=bbox,
            timestamp=1234567890.0,
            frame_id=100
        )
        assert result.detection_type == DetectionType.PERSON
        assert result.bbox == bbox
        assert result.timestamp == 1234567890.0
        assert result.frame_id == 100
    
    def test_pose_keypoint_creation(self):
        """测试姿态关键点创建"""
        keypoint = PoseKeypoint(x=100.0, y=200.0, confidence=0.9, visible=True)
        assert keypoint.x == 100.0
        assert keypoint.y == 200.0
        assert keypoint.confidence == 0.9
        assert keypoint.visible is True
    
    def test_pose_result_creation(self):
        """测试姿态识别结果创建"""
        keypoints = [
            PoseKeypoint(x=100.0, y=200.0, confidence=0.9),
            PoseKeypoint(x=150.0, y=250.0, confidence=0.8)
        ]
        result = PoseResult(
            keypoints=keypoints,
            timestamp=1234567890.0,
            frame_id=100,
            is_fall_detected=True,
            fall_confidence=0.85
        )
        assert len(result.keypoints) == 2
        assert result.is_fall_detected is True
        assert result.fall_confidence == 0.85
    
    def test_alert_event_creation(self):
        """测试报警事件创建"""
        event = AlertEvent(
            alert_type=AlertType.FALL_DETECTED,
            alert_level=AlertLevel.HIGH,
            timestamp=1234567890.0,
            location=(100, 200),
            description="检测到人员跌倒"
        )
        assert event.alert_type == AlertType.FALL_DETECTED
        assert event.alert_level == AlertLevel.HIGH
        assert event.location == (100, 200)
        assert event.description == "检测到人员跌倒"


class TestConfigManager:
    """测试配置管理器"""
    
    def test_config_manager_creation(self):
        """测试配置管理器创建"""
        config_manager = ConfigManager()
        assert config_manager is not None
        assert config_manager.config_dir.exists()
    
    def test_get_config(self):
        """测试获取配置"""
        config_manager = ConfigManager()
        
        # 重置配置到默认值
        config_manager.set_config('confidence_threshold', 0.5)
        
        config = config_manager.get_config()
        assert isinstance(config, SystemConfig)
        
        confidence = config_manager.get_config('confidence_threshold')
        assert confidence == 0.5
    
    def test_set_config(self):
        """测试设置配置"""
        config_manager = ConfigManager()
        result = config_manager.set_config('confidence_threshold', 0.7)
        assert result is True
        
        confidence = config_manager.get_config('confidence_threshold')
        assert confidence == 0.7
    
    def test_update_config(self):
        """测试批量更新配置"""
        config_manager = ConfigManager()
        updates = {
            'confidence_threshold': 0.8,
            'detection_fps': 20
        }
        result = config_manager.update_config(updates)
        assert result is True
        
        assert config_manager.get_config('confidence_threshold') == 0.8
        assert config_manager.get_config('detection_fps') == 20


if __name__ == '__main__':
    pytest.main([__file__])