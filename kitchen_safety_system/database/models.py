"""
数据库模型

定义数据库操作的高级接口。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..core.models import AlertRecord, LogRecord, DetectionStats, UserProfile
from ..utils.logger import get_logger
from .connection import get_db_connection

logger = get_logger(__name__)


class AlertRepository:
    """报警记录仓库"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def create(self, alert: AlertRecord) -> Optional[int]:
        """
        创建报警记录
        
        Args:
            alert: 报警记录对象
            
        Returns:
            创建的记录ID
        """
        return self.db.insert_alert_record(alert)
    
    def get_by_id(self, alert_id: int) -> Optional[AlertRecord]:
        """
        根据ID获取报警记录
        
        Args:
            alert_id: 报警记录ID
            
        Returns:
            报警记录对象
        """
        query = "SELECT * FROM alert_records WHERE id = %s"
        result = self.db.execute_query(query, (alert_id,))
        
        if result:
            return AlertRecord.from_dict(result[0])
        return None
    
    def get_unresolved(self) -> List[AlertRecord]:
        """
        获取未解决的报警记录
        
        Returns:
            未解决的报警记录列表
        """
        query = "SELECT * FROM unresolved_alerts"
        results = self.db.execute_query(query)
        
        return [AlertRecord.from_dict(row) for row in results]
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[AlertRecord]:
        """
        根据日期范围获取报警记录
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            报警记录列表
        """
        query = """
        SELECT * FROM alert_records 
        WHERE timestamp BETWEEN %s AND %s 
        ORDER BY timestamp DESC
        """
        results = self.db.execute_query(query, (start_date, end_date))
        
        return [AlertRecord.from_dict(row) for row in results]
    
    def get_by_type(self, alert_type: str, limit: int = 100) -> List[AlertRecord]:
        """
        根据类型获取报警记录
        
        Args:
            alert_type: 报警类型
            limit: 限制数量
            
        Returns:
            报警记录列表
        """
        query = """
        SELECT * FROM alert_records 
        WHERE alert_type = %s 
        ORDER BY timestamp DESC 
        LIMIT %s
        """
        results = self.db.execute_query(query, (alert_type, limit))
        
        return [AlertRecord.from_dict(row) for row in results]
    
    def resolve(self, alert_id: int, resolved_by: str) -> bool:
        """
        解决报警记录
        
        Args:
            alert_id: 报警记录ID
            resolved_by: 解决者
            
        Returns:
            是否解决成功
        """
        query = """
        UPDATE alert_records 
        SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP, resolved_by = %s 
        WHERE id = %s
        """
        
        try:
            rows_affected = self.db.execute_update(query, (resolved_by, alert_id))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"解决报警记录失败: {e}")
            return False
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        获取报警统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT 
            alert_type,
            alert_level,
            COUNT(*) as count,
            COUNT(CASE WHEN resolved = TRUE THEN 1 END) as resolved_count
        FROM alert_records 
        WHERE timestamp >= %s 
        GROUP BY alert_type, alert_level
        """
        
        results = self.db.execute_query(query, (start_date,))
        
        statistics = {
            'total_alerts': sum(row['count'] for row in results),
            'resolved_alerts': sum(row['resolved_count'] for row in results),
            'by_type': {},
            'by_level': {}
        }
        
        for row in results:
            alert_type = row['alert_type']
            alert_level = row['alert_level']
            
            if alert_type not in statistics['by_type']:
                statistics['by_type'][alert_type] = {'total': 0, 'resolved': 0}
            
            if alert_level not in statistics['by_level']:
                statistics['by_level'][alert_level] = {'total': 0, 'resolved': 0}
            
            statistics['by_type'][alert_type]['total'] += row['count']
            statistics['by_type'][alert_type]['resolved'] += row['resolved_count']
            
            statistics['by_level'][alert_level]['total'] += row['count']
            statistics['by_level'][alert_level]['resolved'] += row['resolved_count']
        
        return statistics


class LogRepository:
    """日志记录仓库"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def create(self, log: LogRecord) -> Optional[int]:
        """
        创建日志记录
        
        Args:
            log: 日志记录对象
            
        Returns:
            创建的记录ID
        """
        return self.db.insert_log_record(log)
    
    def get_by_level(self, level: str, limit: int = 100) -> List[LogRecord]:
        """
        根据级别获取日志记录
        
        Args:
            level: 日志级别
            limit: 限制数量
            
        Returns:
            日志记录列表
        """
        query = """
        SELECT * FROM log_records 
        WHERE level = %s 
        ORDER BY timestamp DESC 
        LIMIT %s
        """
        results = self.db.execute_query(query, (level, limit))
        
        return [LogRecord.from_dict(row) for row in results]
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[LogRecord]:
        """
        根据日期范围获取日志记录
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日志记录列表
        """
        query = """
        SELECT * FROM log_records 
        WHERE timestamp BETWEEN %s AND %s 
        ORDER BY timestamp DESC
        """
        results = self.db.execute_query(query, (start_date, end_date))
        
        return [LogRecord.from_dict(row) for row in results]
    
    def search(self, keyword: str, limit: int = 100) -> List[LogRecord]:
        """
        搜索日志记录
        
        Args:
            keyword: 搜索关键词
            limit: 限制数量
            
        Returns:
            日志记录列表
        """
        query = """
        SELECT * FROM log_records 
        WHERE message ILIKE %s 
        ORDER BY timestamp DESC 
        LIMIT %s
        """
        results = self.db.execute_query(query, (f'%{keyword}%', limit))
        
        return [LogRecord.from_dict(row) for row in results]


class ConfigRepository:
    """配置仓库"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取配置
        
        Args:
            key: 配置键
            
        Returns:
            配置值
        """
        return self.db.get_system_config(key)
    
    def set(self, key: str, value: Dict[str, Any], updated_by: str = 'system') -> bool:
        """
        设置配置
        
        Args:
            key: 配置键
            value: 配置值
            updated_by: 更新者
            
        Returns:
            是否设置成功
        """
        return self.db.set_system_config(key, value, updated_by)
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            所有配置字典
        """
        query = "SELECT config_key, config_value FROM system_configs"
        results = self.db.execute_query(query)
        
        return {row['config_key']: row['config_value'] for row in results}


class StatsRepository:
    """统计仓库"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def save_detection_stats(self, stats: DetectionStats) -> bool:
        """
        保存检测统计
        
        Args:
            stats: 检测统计对象
            
        Returns:
            是否保存成功
        """
        query = """
        INSERT INTO detection_stats (
            total_frames_processed, total_detections, person_detections,
            stove_detections, flame_detections, fall_events,
            unattended_stove_events, average_fps, cpu_usage, memory_usage
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            stats.total_frames_processed,
            stats.total_detections,
            stats.person_detections,
            stats.stove_detections,
            stats.flame_detections,
            stats.fall_events,
            stats.unattended_stove_events,
            stats.average_fps,
            stats.cpu_usage,
            stats.memory_usage
        )
        
        try:
            self.db.execute_update(query, params)
            return True
        except Exception as e:
            logger.error(f"保存检测统计失败: {e}")
            return False
    
    def get_latest_stats(self) -> Optional[DetectionStats]:
        """
        获取最新统计
        
        Returns:
            最新统计对象
        """
        query = "SELECT * FROM latest_detection_stats"
        results = self.db.execute_query(query)
        
        if results:
            row = results[0]
            return DetectionStats(
                total_frames_processed=row['total_frames_processed'],
                total_detections=row['total_detections'],
                person_detections=row['person_detections'],
                stove_detections=row['stove_detections'],
                flame_detections=row['flame_detections'],
                fall_events=row['fall_events'],
                unattended_stove_events=row['unattended_stove_events'],
                average_fps=row['average_fps'],
                cpu_usage=row['cpu_usage'],
                memory_usage=row['memory_usage'],
                last_update_time=row['timestamp']
            )
        return None
    
    def get_today_summary(self) -> Dict[str, Any]:
        """
        获取今日汇总
        
        Returns:
            今日汇总字典
        """
        query = "SELECT * FROM today_stats"
        results = self.db.execute_query(query)
        
        if results:
            return dict(results[0])
        
        return {
            'total_alerts': 0,
            'fall_alerts': 0,
            'stove_alerts': 0,
            'resolved_alerts': 0
        }


# 仓库实例
alert_repo = AlertRepository()
log_repo = LogRepository()
config_repo = ConfigRepository()
stats_repo = StatsRepository()