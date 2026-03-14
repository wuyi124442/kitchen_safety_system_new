"""
缓存管理器

提供Redis缓存的高级接口，专门针对厨房安全检测系统的缓存需求。
"""

import json
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import asdict

from ..core.models import DetectionResult, AlertRecord, SystemConfig
from ..utils.logger import get_logger
from .connection import get_db_connection

logger = get_logger(__name__)


class CacheManager:
    """缓存管理器"""
    
    # 缓存键前缀
    DETECTION_PREFIX = "kitchen_safety:detection"
    CONFIG_PREFIX = "kitchen_safety:config"
    STATS_PREFIX = "kitchen_safety:stats"
    ALERT_PREFIX = "kitchen_safety:alert"
    SYSTEM_PREFIX = "kitchen_safety:system"
    
    # 缓存过期时间（秒）
    DETECTION_TTL = 300      # 检测结果缓存5分钟
    CONFIG_TTL = 3600        # 配置缓存1小时
    STATS_TTL = 60           # 统计数据缓存1分钟
    ALERT_TTL = 1800         # 报警数据缓存30分钟
    SYSTEM_TTL = 300         # 系统状态缓存5分钟
    
    def __init__(self):
        """初始化缓存管理器"""
        self.db = get_db_connection()
    
    def _get_key(self, prefix: str, key: str) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            key: 键名
            
        Returns:
            完整的缓存键
        """
        return f"{prefix}:{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """
        序列化值
        
        Args:
            value: 要序列化的值
            
        Returns:
            序列化后的字符串
        """
        if hasattr(value, '__dict__'):
            # 数据类或对象
            if hasattr(value, 'to_dict'):
                return json.dumps(value.to_dict())
            else:
                return json.dumps(asdict(value))
        elif isinstance(value, (dict, list)):
            return json.dumps(value)
        else:
            return str(value)
    
    def _deserialize_value(self, value: str, value_type: type = None) -> Any:
        """
        反序列化值
        
        Args:
            value: 序列化的字符串或已解析的对象
            value_type: 期望的值类型
            
        Returns:
            反序列化后的值
        """
        try:
            # 如果已经是字典或列表，直接使用
            if isinstance(value, (dict, list)):
                parsed = value
            else:
                parsed = json.loads(value)
            
            if value_type and hasattr(value_type, 'from_dict'):
                return value_type.from_dict(parsed)
            
            return parsed
        except (json.JSONDecodeError, AttributeError, TypeError):
            return value
    
    # 检测结果缓存
    def cache_detection_result(self, frame_id: str, result: DetectionResult) -> bool:
        """
        缓存检测结果
        
        Args:
            frame_id: 帧ID
            result: 检测结果
            
        Returns:
            是否缓存成功
        """
        key = self._get_key(self.DETECTION_PREFIX, f"frame:{frame_id}")
        value = self._serialize_value(result)
        
        return self.db.cache_set(key, value, self.DETECTION_TTL)
    
    def get_detection_result(self, frame_id: str) -> Optional[DetectionResult]:
        """
        获取检测结果
        
        Args:
            frame_id: 帧ID
            
        Returns:
            检测结果对象
        """
        key = self._get_key(self.DETECTION_PREFIX, f"frame:{frame_id}")
        value = self.db.cache_get(key)
        
        if value:
            return self._deserialize_value(value, DetectionResult)
        
        return None
    
    def cache_latest_detections(self, detections: List[DetectionResult], max_count: int = 100) -> bool:
        """
        缓存最新的检测结果列表
        
        Args:
            detections: 检测结果列表
            max_count: 最大缓存数量
            
        Returns:
            是否缓存成功
        """
        # 只保留最新的检测结果
        latest_detections = detections[-max_count:] if len(detections) > max_count else detections
        
        key = self._get_key(self.DETECTION_PREFIX, "latest")
        value = self._serialize_value([asdict(d) for d in latest_detections])
        
        return self.db.cache_set(key, value, self.DETECTION_TTL)
    
    def get_latest_detections(self) -> List[DetectionResult]:
        """
        获取最新的检测结果列表
        
        Returns:
            检测结果列表
        """
        key = self._get_key(self.DETECTION_PREFIX, "latest")
        value = self.db.cache_get(key)
        
        if value and isinstance(value, list):
            return [DetectionResult.from_dict(d) for d in value]
        
        return []
    
    # 系统配置缓存
    def cache_system_config(self, config_key: str, config_value: Dict[str, Any]) -> bool:
        """
        缓存系统配置
        
        Args:
            config_key: 配置键
            config_value: 配置值
            
        Returns:
            是否缓存成功
        """
        key = self._get_key(self.CONFIG_PREFIX, config_key)
        value = self._serialize_value(config_value)
        
        return self.db.cache_set(key, value, self.CONFIG_TTL)
    
    def get_system_config(self, config_key: str) -> Optional[Dict[str, Any]]:
        """
        获取系统配置
        
        Args:
            config_key: 配置键
            
        Returns:
            配置值字典
        """
        key = self._get_key(self.CONFIG_PREFIX, config_key)
        value = self.db.cache_get(key)
        
        if value:
            return self._deserialize_value(value)
        
        return None
    
    def invalidate_config_cache(self, config_key: str = None) -> bool:
        """
        使配置缓存失效
        
        Args:
            config_key: 配置键，如果为None则清除所有配置缓存
            
        Returns:
            是否操作成功
        """
        if config_key:
            key = self._get_key(self.CONFIG_PREFIX, config_key)
            return self.db.cache_delete(key)
        else:
            # 清除所有配置缓存
            # 注意：这里简化实现，实际应该使用Redis的SCAN命令
            common_configs = [
                'detection_settings', 'risk_monitoring', 'alert_settings',
                'video_settings', 'performance_settings'
            ]
            
            success = True
            for config in common_configs:
                key = self._get_key(self.CONFIG_PREFIX, config)
                if not self.db.cache_delete(key):
                    success = False
            
            return success
    
    # 统计数据缓存
    def cache_detection_stats(self, stats: Dict[str, Any]) -> bool:
        """
        缓存检测统计数据
        
        Args:
            stats: 统计数据字典
            
        Returns:
            是否缓存成功
        """
        key = self._get_key(self.STATS_PREFIX, "detection")
        value = self._serialize_value(stats)
        
        return self.db.cache_set(key, value, self.STATS_TTL)
    
    def get_detection_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取检测统计数据
        
        Returns:
            统计数据字典
        """
        key = self._get_key(self.STATS_PREFIX, "detection")
        value = self.db.cache_get(key)
        
        if value:
            return self._deserialize_value(value)
        
        return None
    
    def cache_system_performance(self, performance: Dict[str, float]) -> bool:
        """
        缓存系统性能数据
        
        Args:
            performance: 性能数据字典
            
        Returns:
            是否缓存成功
        """
        key = self._get_key(self.STATS_PREFIX, "performance")
        value = self._serialize_value(performance)
        
        return self.db.cache_set(key, value, self.SYSTEM_TTL)
    
    def get_system_performance(self) -> Optional[Dict[str, float]]:
        """
        获取系统性能数据
        
        Returns:
            性能数据字典
        """
        key = self._get_key(self.STATS_PREFIX, "performance")
        value = self.db.cache_get(key)
        
        if value:
            return self._deserialize_value(value)
        
        return None
    
    # 报警数据缓存
    def cache_recent_alerts(self, alerts: List[AlertRecord], max_count: int = 50) -> bool:
        """
        缓存最近的报警记录
        
        Args:
            alerts: 报警记录列表
            max_count: 最大缓存数量
            
        Returns:
            是否缓存成功
        """
        # 只保留最新的报警记录
        recent_alerts = alerts[-max_count:] if len(alerts) > max_count else alerts
        
        key = self._get_key(self.ALERT_PREFIX, "recent")
        value = self._serialize_value([asdict(a) for a in recent_alerts])
        
        return self.db.cache_set(key, value, self.ALERT_TTL)
    
    def get_recent_alerts(self) -> List[AlertRecord]:
        """
        获取最近的报警记录
        
        Returns:
            报警记录列表
        """
        key = self._get_key(self.ALERT_PREFIX, "recent")
        value = self.db.cache_get(key)
        
        if value and isinstance(value, list):
            return [AlertRecord.from_dict(a) for a in value]
        
        return []
    
    def cache_alert_summary(self, summary: Dict[str, Any]) -> bool:
        """
        缓存报警汇总数据
        
        Args:
            summary: 汇总数据字典
            
        Returns:
            是否缓存成功
        """
        key = self._get_key(self.ALERT_PREFIX, "summary")
        value = self._serialize_value(summary)
        
        return self.db.cache_set(key, value, self.ALERT_TTL)
    
    def get_alert_summary(self) -> Optional[Dict[str, Any]]:
        """
        获取报警汇总数据
        
        Returns:
            汇总数据字典
        """
        key = self._get_key(self.ALERT_PREFIX, "summary")
        value = self.db.cache_get(key)
        
        if value:
            return self._deserialize_value(value)
        
        return None
    
    # 系统状态缓存
    def cache_system_status(self, status: Dict[str, Any]) -> bool:
        """
        缓存系统状态
        
        Args:
            status: 系统状态字典
            
        Returns:
            是否缓存成功
        """
        key = self._get_key(self.SYSTEM_PREFIX, "status")
        value = self._serialize_value(status)
        
        return self.db.cache_set(key, value, self.SYSTEM_TTL)
    
    def get_system_status(self) -> Optional[Dict[str, Any]]:
        """
        获取系统状态
        
        Returns:
            系统状态字典
        """
        key = self._get_key(self.SYSTEM_PREFIX, "status")
        value = self.db.cache_get(key)
        
        if value:
            return self._deserialize_value(value)
        
        return None
    
    # 实时数据流缓存
    def push_realtime_data(self, data_type: str, data: Dict[str, Any], max_length: int = 1000) -> bool:
        """
        推送实时数据到Redis列表
        
        Args:
            data_type: 数据类型
            data: 数据字典
            max_length: 列表最大长度
            
        Returns:
            是否推送成功
        """
        try:
            if not self.db.redis_connection:
                if not self.db.connect_redis():
                    return False
            
            key = self._get_key("realtime", data_type)
            value = self._serialize_value(data)
            
            # 添加时间戳
            timestamped_data = {
                'timestamp': time.time(),
                'data': data
            }
            
            # 推送到列表头部
            self.db.redis_connection.lpush(key, self._serialize_value(timestamped_data))
            
            # 保持列表长度
            self.db.redis_connection.ltrim(key, 0, max_length - 1)
            
            # 设置过期时间
            self.db.redis_connection.expire(key, self.DETECTION_TTL)
            
            return True
            
        except Exception as e:
            logger.error(f"推送实时数据失败: {e}")
            return False
    
    def get_realtime_data(self, data_type: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取实时数据
        
        Args:
            data_type: 数据类型
            count: 获取数量
            
        Returns:
            实时数据列表
        """
        try:
            if not self.db.redis_connection:
                if not self.db.connect_redis():
                    return []
            
            key = self._get_key("realtime", data_type)
            
            # 从列表头部获取数据
            raw_data = self.db.redis_connection.lrange(key, 0, count - 1)
            
            result = []
            for item in raw_data:
                try:
                    parsed = self._deserialize_value(item.decode('utf-8'))
                    result.append(parsed)
                except Exception as e:
                    logger.warning(f"解析实时数据失败: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return []
    
    # 缓存清理
    def clear_cache(self, prefix: str = None) -> bool:
        """
        清理缓存
        
        Args:
            prefix: 缓存前缀，如果为None则清理所有缓存
            
        Returns:
            是否清理成功
        """
        try:
            if not self.db.redis_connection:
                if not self.db.connect_redis():
                    return False
            
            if prefix:
                # 清理指定前缀的缓存
                pattern = f"{prefix}:*"
                keys = self.db.redis_connection.keys(pattern)
                if keys:
                    self.db.redis_connection.delete(*keys)
            else:
                # 清理所有厨房安全系统相关的缓存
                pattern = "kitchen_safety:*"
                keys = self.db.redis_connection.keys(pattern)
                if keys:
                    self.db.redis_connection.delete(*keys)
            
            logger.info(f"缓存清理完成，前缀: {prefix or 'all'}")
            return True
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Returns:
            缓存信息字典
        """
        try:
            if not self.db.redis_connection:
                if not self.db.connect_redis():
                    return {}
            
            info = self.db.redis_connection.info()
            
            # 统计各类型缓存的键数量
            prefixes = [
                self.DETECTION_PREFIX,
                self.CONFIG_PREFIX,
                self.STATS_PREFIX,
                self.ALERT_PREFIX,
                self.SYSTEM_PREFIX
            ]
            
            key_counts = {}
            for prefix in prefixes:
                pattern = f"{prefix}:*"
                keys = self.db.redis_connection.keys(pattern)
                key_counts[prefix] = len(keys)
            
            return {
                'redis_info': {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                },
                'key_counts': key_counts,
                'total_keys': sum(key_counts.values())
            }
            
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {}


# 全局缓存管理器实例
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    return cache_manager