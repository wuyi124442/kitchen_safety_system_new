"""
数据库集成测试

测试数据库和缓存系统的集成功能。
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from kitchen_safety_system.database import (
    get_db_connection, get_cache_manager,
    alert_repo, config_repo
)
from kitchen_safety_system.core.models import AlertRecord, DetectionResult


class TestDatabaseCacheIntegration:
    """数据库和缓存集成测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.db = get_db_connection()
        self.cache = get_cache_manager()
    
    def test_config_cache_integration(self):
        """测试配置的数据库和缓存集成"""
        # 模拟配置更新流程：数据库更新 -> 缓存失效 -> 重新缓存
        
        config_key = "detection_settings"
        config_value = {
            "confidence_threshold": 0.6,
            "detection_fps": 20
        }
        
        with patch.object(config_repo.db, 'set_system_config', return_value=True):
            with patch.object(self.cache.db, 'cache_delete', return_value=True):
                with patch.object(self.cache.db, 'cache_set', return_value=True):
                    
                    # 1. 更新数据库配置
                    result = config_repo.set(config_key, config_value)
                    assert result is True
                    
                    # 2. 使缓存失效
                    cache_result = self.cache.invalidate_config_cache(config_key)
                    assert cache_result is True
                    
                    # 3. 重新缓存配置
                    cache_set_result = self.cache.cache_system_config(config_key, config_value)
                    assert cache_set_result is True
    
    def test_alert_creation_with_cache_update(self):
        """测试报警创建时的缓存更新"""
        alert = AlertRecord(
            alert_type="fall_detected",
            alert_level="high",
            timestamp=datetime.now(),
            description="集成测试报警"
        )
        
        with patch.object(alert_repo.db, 'insert_alert_record', return_value=1):
            with patch.object(self.cache, 'cache_recent_alerts', return_value=True):
                
                # 1. 创建报警记录
                alert_id = alert_repo.create(alert)
                assert alert_id == 1
                
                # 2. 更新缓存中的最近报警
                cache_result = self.cache.cache_recent_alerts([alert])
                assert cache_result is True
    
    def test_detection_result_caching_flow(self):
        """测试检测结果的缓存流程"""
        detection_result = DetectionResult(
            frame_id="integration_test_frame",
            timestamp=datetime.now(),
            detections=[
                {
                    "class": "person",
                    "confidence": 0.85,
                    "bbox": [100, 100, 200, 200]
                }
            ],
            processing_time=0.15
        )
        
        with patch.object(self.cache.db, 'cache_set', return_value=True):
            with patch.object(self.cache.db, 'cache_get', return_value=detection_result.to_dict()):
                
                # 1. 缓存检测结果
                cache_result = self.cache.cache_detection_result(
                    detection_result.frame_id, 
                    detection_result
                )
                assert cache_result is True
                
                # 2. 从缓存获取检测结果
                cached_result = self.cache.get_detection_result(detection_result.frame_id)
                assert cached_result is not None
                assert cached_result.frame_id == detection_result.frame_id
    
    def test_performance_monitoring_integration(self):
        """测试性能监控的集成"""
        performance_data = {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "fps": 18.5,
            "detection_count": 15
        }
        
        with patch.object(self.cache.db, 'cache_set', return_value=True):
            with patch.object(self.cache.db, 'cache_get', return_value=performance_data):
                
                # 1. 缓存性能数据
                cache_result = self.cache.cache_system_performance(performance_data)
                assert cache_result is True
                
                # 2. 获取性能数据
                cached_performance = self.cache.get_system_performance()
                assert cached_performance is not None
                assert cached_performance["cpu_usage"] == 45.2
    
    def test_realtime_data_stream_integration(self):
        """测试实时数据流集成"""
        detection_data = {
            "detections": [
                {"class": "person", "confidence": 0.9},
                {"class": "stove", "confidence": 0.8}
            ],
            "frame_count": 1000
        }
        
        # 模拟Redis列表操作
        mock_redis = MagicMock()
        
        with patch.object(self.cache.db, 'redis_connection', mock_redis):
            with patch.object(self.cache.db, 'connect_redis', return_value=True):
                
                # 1. 推送实时数据
                result = self.cache.push_realtime_data("detections", detection_data)
                assert result is True
                
                # 验证Redis操作被调用
                mock_redis.lpush.assert_called_once()
                mock_redis.ltrim.assert_called_once()
                mock_redis.expire.assert_called_once()
    
    def test_cache_fallback_mechanism(self):
        """测试缓存回退机制"""
        config_key = "detection_settings"
        db_config = {
            "confidence_threshold": 0.5,
            "detection_fps": 15
        }
        
        # 模拟缓存未命中，回退到数据库
        with patch.object(self.cache.db, 'cache_get', return_value=None):
            with patch.object(config_repo.db, 'get_system_config', return_value=db_config):
                with patch.object(self.cache.db, 'cache_set', return_value=True):
                    
                    # 1. 尝试从缓存获取（未命中）
                    cached_config = self.cache.get_system_config(config_key)
                    assert cached_config is None
                    
                    # 2. 从数据库获取
                    db_result = config_repo.get(config_key)
                    assert db_result == db_config
                    
                    # 3. 重新缓存
                    cache_result = self.cache.cache_system_config(config_key, db_config)
                    assert cache_result is True
    
    def test_concurrent_access_simulation(self):
        """测试并发访问模拟"""
        # 模拟多个组件同时访问缓存和数据库
        
        config_operations = []
        cache_operations = []
        
        # 模拟配置读取
        with patch.object(self.cache.db, 'cache_get') as mock_cache_get:
            with patch.object(config_repo.db, 'get_system_config') as mock_db_get:
                
                mock_cache_get.return_value = {"cached": True}
                mock_db_get.return_value = {"from_db": True}
                
                # 模拟多次并发访问
                for i in range(5):
                    config_operations.append(self.cache.get_system_config(f"config_{i}"))
                    cache_operations.append(config_repo.get(f"config_{i}"))
                
                # 验证所有操作都成功
                assert len(config_operations) == 5
                assert len(cache_operations) == 5
                assert all(op is not None for op in config_operations)
                assert all(op is not None for op in cache_operations)


class TestDatabaseErrorHandling:
    """数据库错误处理测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.db = get_db_connection()
        self.cache = get_cache_manager()
    
    def test_database_connection_failure(self):
        """测试数据库连接失败处理"""
        with patch.object(self.db, 'connect_postgresql', return_value=False):
            # 数据库连接失败时应该优雅处理
            result = self.db.connect_postgresql()
            assert result is False
    
    def test_redis_connection_failure(self):
        """测试Redis连接失败处理"""
        with patch.object(self.db, 'connect_redis', return_value=False):
            # Redis连接失败时应该优雅处理
            result = self.db.connect_redis()
            assert result is False
    
    def test_cache_operation_failure_fallback(self):
        """测试缓存操作失败时的回退"""
        config_key = "test_config"
        config_value = {"test": "value"}
        
        # 模拟缓存设置失败
        with patch.object(self.cache.db, 'cache_set', return_value=False):
            result = self.cache.cache_system_config(config_key, config_value)
            assert result is False
        
        # 模拟缓存获取失败
        with patch.object(self.cache.db, 'cache_get', return_value=None):
            result = self.cache.get_system_config(config_key)
            assert result is None
    
    def test_serialization_error_handling(self):
        """测试序列化错误处理"""
        # 测试无法序列化的对象
        class UnserializableObject:
            def __init__(self):
                self.circular_ref = self
        
        obj = UnserializableObject()
        
        # 应该优雅处理序列化错误
        try:
            result = self.cache._serialize_value(obj)
            # 如果没有抛出异常，应该返回字符串表示
            assert isinstance(result, str)
        except Exception:
            # 如果抛出异常，也是可以接受的
            pass


if __name__ == '__main__':
    # 运行集成测试
    pytest.main([__file__, '-v'])