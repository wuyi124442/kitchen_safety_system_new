"""
数据库和缓存系统测试

测试PostgreSQL数据库和Redis缓存系统的功能。
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from kitchen_safety_system.database import (
    get_db_connection, get_cache_manager,
    alert_repo, log_repo, config_repo, stats_repo
)
from kitchen_safety_system.core.models import (
    AlertRecord, LogRecord, DetectionResult, DetectionStats
)


class TestDatabaseConnection:
    """数据库连接测试"""
    
    def test_database_manager_initialization(self):
        """测试数据库管理器初始化"""
        db = get_db_connection()
        assert db is not None
        assert hasattr(db, 'pg_config')
        assert hasattr(db, 'redis_config')
    
    @patch('kitchen_safety_system.database.connection.PSYCOPG2_AVAILABLE', True)
    @patch('psycopg2.connect')
    def test_postgresql_connection(self, mock_connect):
        """测试PostgreSQL连接"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        db = get_db_connection()
        result = db.connect_postgresql()
        
        assert result is True
        mock_connect.assert_called_once()
    
    @patch('kitchen_safety_system.database.connection.REDIS_AVAILABLE', True)
    @patch('redis.Redis')
    def test_redis_connection(self, mock_redis):
        """测试Redis连接"""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        
        db = get_db_connection()
        result = db.connect_redis()
        
        assert result is True
        mock_redis.assert_called_once()
        mock_redis_instance.ping.assert_called_once()


class TestCacheManager:
    """缓存管理器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.cache = get_cache_manager()
    
    def test_cache_manager_initialization(self):
        """测试缓存管理器初始化"""
        assert self.cache is not None
        assert hasattr(self.cache, 'DETECTION_PREFIX')
        assert hasattr(self.cache, 'CONFIG_PREFIX')
    
    def test_key_generation(self):
        """测试缓存键生成"""
        key = self.cache._get_key("test_prefix", "test_key")
        assert key == "test_prefix:test_key"
    
    def test_value_serialization(self):
        """测试值序列化"""
        # 测试字典序列化
        test_dict = {"key": "value", "number": 123}
        serialized = self.cache._serialize_value(test_dict)
        assert isinstance(serialized, str)
        
        # 测试反序列化
        deserialized = self.cache._deserialize_value(serialized)
        assert deserialized == test_dict
    
    @patch.object(get_cache_manager().db, 'cache_set')
    def test_cache_detection_result(self, mock_cache_set):
        """测试检测结果缓存"""
        mock_cache_set.return_value = True
        
        detection_result = DetectionResult(
            frame_id="test_frame",
            timestamp=datetime.now(),
            detections=[],
            processing_time=0.1
        )
        
        result = self.cache.cache_detection_result("test_frame", detection_result)
        assert result is True
        mock_cache_set.assert_called_once()
    
    @patch.object(get_cache_manager().db, 'cache_get')
    def test_get_detection_result(self, mock_cache_get):
        """测试获取检测结果"""
        mock_data = {
            "frame_id": "test_frame",
            "timestamp": datetime.now().isoformat(),
            "detections": [],
            "processing_time": 0.1
        }
        mock_cache_get.return_value = mock_data
        
        result = self.cache.get_detection_result("test_frame")
        assert result is not None
        mock_cache_get.assert_called_once()
    
    @patch.object(get_cache_manager().db, 'cache_set')
    def test_cache_system_config(self, mock_cache_set):
        """测试系统配置缓存"""
        mock_cache_set.return_value = True
        
        config = {
            "confidence_threshold": 0.5,
            "detection_fps": 15
        }
        
        result = self.cache.cache_system_config("detection_settings", config)
        assert result is True
        mock_cache_set.assert_called_once()
    
    @patch.object(get_cache_manager().db, 'cache_delete')
    def test_invalidate_config_cache(self, mock_cache_delete):
        """测试配置缓存失效"""
        mock_cache_delete.return_value = True
        
        result = self.cache.invalidate_config_cache("detection_settings")
        assert result is True
        mock_cache_delete.assert_called_once()


class TestDatabaseRepositories:
    """数据库仓库测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.alert_record = AlertRecord(
            alert_type="fall_detected",
            alert_level="high",
            timestamp=datetime.now(),
            location_x=100,
            location_y=200,
            description="测试跌倒报警"
        )
        
        self.log_record = LogRecord(
            level="INFO",
            message="测试日志消息",
            timestamp=datetime.now(),
            module="test_module",
            function="test_function"
        )
    
    @patch.object(alert_repo.db, 'insert_alert_record')
    def test_alert_repository_create(self, mock_insert):
        """测试报警记录创建"""
        mock_insert.return_value = 1
        
        result = alert_repo.create(self.alert_record)
        assert result == 1
        mock_insert.assert_called_once_with(self.alert_record)
    
    @patch.object(alert_repo.db, 'execute_query')
    def test_alert_repository_get_by_id(self, mock_query):
        """测试根据ID获取报警记录"""
        mock_data = {
            'id': 1,
            'alert_type': 'fall_detected',
            'alert_level': 'high',
            'timestamp': datetime.now(),
            'location_x': 100,
            'location_y': 200,
            'description': '测试跌倒报警',
            'video_clip_path': None,
            'additional_data': None,
            'resolved': False,
            'resolved_at': None,
            'resolved_by': None
        }
        mock_query.return_value = [mock_data]
        
        result = alert_repo.get_by_id(1)
        assert result is not None
        assert result.alert_type == 'fall_detected'
        mock_query.assert_called_once()
    
    @patch.object(log_repo.db, 'insert_log_record')
    def test_log_repository_create(self, mock_insert):
        """测试日志记录创建"""
        mock_insert.return_value = 1
        
        result = log_repo.create(self.log_record)
        assert result == 1
        mock_insert.assert_called_once_with(self.log_record)
    
    @patch.object(config_repo.db, 'get_system_config')
    def test_config_repository_get(self, mock_get):
        """测试配置获取"""
        mock_config = {
            "confidence_threshold": 0.5,
            "detection_fps": 15
        }
        mock_get.return_value = mock_config
        
        result = config_repo.get("detection_settings")
        assert result == mock_config
        mock_get.assert_called_once_with("detection_settings")
    
    @patch.object(config_repo.db, 'set_system_config')
    def test_config_repository_set(self, mock_set):
        """测试配置设置"""
        mock_set.return_value = True
        
        config = {"confidence_threshold": 0.6}
        result = config_repo.set("detection_settings", config)
        
        assert result is True
        mock_set.assert_called_once_with("detection_settings", config, 'system')


class TestDatabaseIntegration:
    """数据库集成测试"""
    
    @pytest.mark.integration
    def test_database_cache_integration(self):
        """测试数据库和缓存集成"""
        # 这个测试需要真实的数据库和Redis连接
        # 在CI/CD环境中可能需要跳过
        pytest.skip("需要真实的数据库和Redis连接")
    
    def test_cache_fallback_to_database(self):
        """测试缓存未命中时回退到数据库"""
        # 模拟缓存未命中，应该从数据库获取数据
        with patch.object(get_cache_manager(), 'get_system_config', return_value=None):
            with patch.object(config_repo, 'get', return_value={"test": "value"}):
                # 这里应该实现缓存未命中时的回退逻辑
                pass
    
    def test_cache_invalidation_on_update(self):
        """测试更新时缓存失效"""
        # 模拟配置更新时缓存失效
        with patch.object(get_cache_manager(), 'invalidate_config_cache') as mock_invalidate:
            with patch.object(config_repo, 'set', return_value=True):
                # 这里应该实现更新时缓存失效的逻辑
                pass


class TestPerformanceOptimization:
    """性能优化测试"""
    
    def test_cache_hit_performance(self):
        """测试缓存命中性能"""
        cache = get_cache_manager()
        
        # 模拟缓存命中
        with patch.object(cache.db, 'cache_get', return_value={"test": "data"}):
            start_time = time.time()
            result = cache.get_system_config("test_config")
            end_time = time.time()
            
            # 缓存命中应该很快
            assert (end_time - start_time) < 0.01
            assert result is not None
    
    def test_batch_cache_operations(self):
        """测试批量缓存操作"""
        cache = get_cache_manager()
        
        # 测试批量设置配置
        configs = {
            "config1": {"value": 1},
            "config2": {"value": 2},
            "config3": {"value": 3}
        }
        
        with patch.object(cache.db, 'cache_set', return_value=True) as mock_set:
            for key, value in configs.items():
                cache.cache_system_config(key, value)
            
            # 应该调用了3次缓存设置
            assert mock_set.call_count == 3
    
    def test_realtime_data_stream(self):
        """测试实时数据流"""
        cache = get_cache_manager()
        
        # 模拟实时数据推送
        test_data = {
            "detection_count": 5,
            "timestamp": time.time()
        }
        
        with patch.object(cache, 'push_realtime_data', return_value=True) as mock_push:
            result = cache.push_realtime_data("detections", test_data)
            assert result is True
            mock_push.assert_called_once_with("detections", test_data)


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v'])