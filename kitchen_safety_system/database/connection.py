"""
数据库连接管理

提供PostgreSQL和Redis连接管理功能。
"""

import os
import json
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dataclasses import asdict

# Redis配置选项
REDIS_DISABLED = os.environ.get('REDIS_DISABLED', 'False').lower() == 'true'

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..utils.logger import get_logger
from ..core.models import AlertRecord, LogRecord, SystemConfig

logger = get_logger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        """初始化数据库管理器"""
        self.pg_connection = None
        self.redis_connection = None
        
        # PostgreSQL配置
        self.pg_config = {
            'host': os.getenv('DATABASE_HOST', 'localhost'),
            'port': int(os.getenv('DATABASE_PORT', 5432)),
            'database': os.getenv('DATABASE_NAME', 'kitchen_safety'),
            'user': os.getenv('DATABASE_USER', 'kitchen_user'),
            'password': os.getenv('DATABASE_PASSWORD', 'kitchen_pass')
        }
        
        # Redis配置
        self.redis_config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'db': int(os.getenv('REDIS_DB', 0)),
            'password': os.getenv('REDIS_PASSWORD') or None
        }
    
    def connect_postgresql(self) -> bool:
        """
        连接PostgreSQL数据库
        
        Returns:
            是否连接成功
        """
        if not PSYCOPG2_AVAILABLE:
            logger.error("psycopg2未安装，无法连接PostgreSQL")
            return False
        
        try:
            self.pg_connection = psycopg2.connect(**self.pg_config)
            logger.info("PostgreSQL连接成功")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL连接失败: {e}")
            return False
    
    def connect_redis(self) -> bool:
        """
        连接Redis数据库
        
        Returns:
            是否连接成功
        """
        if REDIS_DISABLED:
            logger.info("Redis已禁用，跳过连接")
            return False
            
        if not REDIS_AVAILABLE:
            logger.warning("redis未安装，无法连接Redis")
            return False
        
        try:
            self.redis_connection = redis.Redis(**self.redis_config)
            # 测试连接
            self.redis_connection.ping()
            logger.info("Redis连接成功")
            return True
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}，系统将在无缓存模式下运行")
            return False
    
    @contextmanager
    def get_pg_cursor(self):
        """
        获取PostgreSQL游标上下文管理器
        
        Yields:
            数据库游标
        """
        if not self.pg_connection:
            if not self.connect_postgresql():
                raise Exception("无法连接到PostgreSQL数据库")
        
        try:
            cursor = self.pg_connection.cursor(cursor_factory=RealDictCursor)
            yield cursor
            self.pg_connection.commit()
        except Exception as e:
            self.pg_connection.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        with self.get_pg_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        执行更新语句
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            影响的行数
        """
        with self.get_pg_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def insert_alert_record(self, alert: AlertRecord) -> Optional[int]:
        """
        插入报警记录
        
        Args:
            alert: 报警记录对象
            
        Returns:
            插入记录的ID
        """
        query = """
        INSERT INTO alert_records (
            alert_type, alert_level, timestamp, location_x, location_y,
            description, video_clip_path, additional_data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            alert.alert_type,
            alert.alert_level,
            alert.timestamp,
            alert.location_x,
            alert.location_y,
            alert.description,
            alert.video_clip_path,
            json.dumps(alert.additional_data) if alert.additional_data else None
        )
        
        try:
            with self.get_pg_cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result['id'] if result else None
        except Exception as e:
            logger.error(f"插入报警记录失败: {e}")
            return None
    
    def insert_log_record(self, log: LogRecord) -> Optional[int]:
        """
        插入日志记录
        
        Args:
            log: 日志记录对象
            
        Returns:
            插入记录的ID
        """
        query = """
        INSERT INTO log_records (
            level, message, timestamp, module, function, line_number, additional_data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            log.level,
            log.message,
            log.timestamp,
            log.module,
            log.function,
            log.line_number,
            json.dumps(log.additional_data) if log.additional_data else None
        )
        
        try:
            with self.get_pg_cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result['id'] if result else None
        except Exception as e:
            logger.error(f"插入日志记录失败: {e}")
            return None
    
    def get_system_config(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取系统配置
        
        Args:
            key: 配置键名
            
        Returns:
            配置值字典
        """
        query = "SELECT config_value FROM system_configs WHERE config_key = %s"
        
        try:
            result = self.execute_query(query, (key,))
            if result:
                return result[0]['config_value']
            return None
        except Exception as e:
            logger.error(f"获取系统配置失败: {e}")
            return None
    
    def set_system_config(self, key: str, value: Dict[str, Any], updated_by: str = 'system') -> bool:
        """
        设置系统配置
        
        Args:
            key: 配置键名
            value: 配置值
            updated_by: 更新者
            
        Returns:
            是否设置成功
        """
        query = """
        INSERT INTO system_configs (config_key, config_value, updated_by)
        VALUES (%s, %s, %s)
        ON CONFLICT (config_key) 
        DO UPDATE SET config_value = EXCLUDED.config_value, 
                     updated_at = CURRENT_TIMESTAMP,
                     updated_by = EXCLUDED.updated_by
        """
        
        try:
            self.execute_update(query, (key, json.dumps(value), updated_by))
            return True
        except Exception as e:
            logger.error(f"设置系统配置失败: {e}")
            return False
    
    def cache_set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """
        设置Redis缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        if not self.redis_connection:
            if not self.connect_redis():
                return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            self.redis_connection.setex(key, expire, value)
            return True
        except Exception as e:
            logger.error(f"设置Redis缓存失败: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[Any]:
        """
        获取Redis缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值
        """
        if not self.redis_connection:
            if not self.connect_redis():
                return None
        
        try:
            value = self.redis_connection.get(key)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return value.decode('utf-8')
        except Exception as e:
            logger.error(f"获取Redis缓存失败: {e}")
            return None
    
    def cache_delete(self, key: str) -> bool:
        """
        删除Redis缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if not self.redis_connection:
            if not self.connect_redis():
                return False
        
        try:
            self.redis_connection.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除Redis缓存失败: {e}")
            return False
    
    def close_connections(self):
        """关闭所有数据库连接"""
        if self.pg_connection:
            self.pg_connection.close()
            self.pg_connection = None
            logger.info("PostgreSQL连接已关闭")
        
        if self.redis_connection:
            self.redis_connection.close()
            self.redis_connection = None
            logger.info("Redis连接已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db_connection():
    """获取数据库连接管理器"""
    return db_manager