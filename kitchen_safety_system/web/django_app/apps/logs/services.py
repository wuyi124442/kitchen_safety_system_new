"""
日志服务模块
提供日志记录和查询的业务逻辑
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import LogEntry
from ....core.models import LogRecord
from ....database.models import log_repo

User = get_user_model()


class LogService:
    """日志服务类"""
    
    @staticmethod
    def create_log_entry(
        level: str,
        log_type: str,
        message: str,
        module: Optional[str] = None,
        function: Optional[str] = None,
        line_number: Optional[int] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        user: Optional[User] = None
    ) -> LogEntry:
        """
        创建日志条目
        
        Args:
            level: 日志级别
            log_type: 日志类型
            message: 日志消息
            module: 模块名
            function: 函数名
            line_number: 行号
            additional_data: 附加数据
            user: 用户对象
            
        Returns:
            创建的日志条目
        """
        with transaction.atomic():
            # 创建Django模型记录
            log_entry = LogEntry.objects.create(
                level=level,
                log_type=log_type,
                message=message,
                module=module,
                function=function,
                line_number=line_number,
                additional_data=additional_data,
                user=user
            )
            
            # 同时创建核心系统日志记录
            log_record = LogRecord(
                level=level,
                message=message,
                timestamp=log_entry.timestamp,
                module=module,
                function=function,
                line_number=line_number,
                additional_data=additional_data
            )
            
            # 保存到核心日志系统
            log_repo.create(log_record)
            
            return log_entry
    
    @staticmethod
    def sync_from_core_logs(limit: int = 1000) -> int:
        """
        从核心日志系统同步日志到Django模型
        
        Args:
            limit: 同步数量限制
            
        Returns:
            同步的日志数量
        """
        # 获取最新的Django日志时间戳
        latest_django_log = LogEntry.objects.order_by('-timestamp').first()
        since_time = latest_django_log.timestamp if latest_django_log else datetime.now() - timedelta(days=7)
        
        # 从核心系统获取新日志
        core_logs = log_repo.get_by_date_range(since_time, datetime.now())
        
        synced_count = 0
        
        with transaction.atomic():
            for log_record in core_logs[:limit]:
                # 检查是否已存在
                if not LogEntry.objects.filter(
                    timestamp=log_record.timestamp,
                    message=log_record.message,
                    level=log_record.level
                ).exists():
                    
                    # 映射日志类型
                    log_type = LogService._map_log_type(log_record.module, log_record.message)
                    
                    LogEntry.objects.create(
                        level=log_record.level,
                        log_type=log_type,
                        message=log_record.message,
                        timestamp=log_record.timestamp,
                        module=log_record.module,
                        function=log_record.function,
                        line_number=log_record.line_number,
                        additional_data=log_record.additional_data
                    )
                    
                    synced_count += 1
        
        return synced_count
    
    @staticmethod
    def _map_log_type(module: Optional[str], message: str) -> str:
        """
        根据模块和消息内容映射日志类型
        
        Args:
            module: 模块名
            message: 日志消息
            
        Returns:
            日志类型
        """
        if not module:
            return 'SYSTEM'
        
        module_lower = module.lower()
        message_lower = message.lower()
        
        # 检测模块映射
        if 'detection' in module_lower or 'yolo' in module_lower or 'pose' in module_lower:
            return 'DETECTION'
        elif 'alert' in module_lower or 'notification' in module_lower:
            return 'ALERT'
        elif 'auth' in module_lower or 'user' in module_lower:
            return 'USER'
        elif 'error' in message_lower or 'exception' in message_lower or 'failed' in message_lower:
            return 'ERROR'
        else:
            return 'SYSTEM'
    
    @staticmethod
    def get_log_statistics(days: int = 7) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        queryset = LogEntry.objects.filter(timestamp__gte=start_date)
        
        # 按级别统计
        level_stats = {}
        for choice in LogEntry.LEVEL_CHOICES:
            level = choice[0]
            count = queryset.filter(level=level).count()
            level_stats[level] = count
        
        # 按类型统计
        type_stats = {}
        for choice in LogEntry.TYPE_CHOICES:
            log_type = choice[0]
            count = queryset.filter(log_type=log_type).count()
            type_stats[log_type] = count
        
        # 按天统计
        daily_stats = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = queryset.filter(
                timestamp__gte=day_start,
                timestamp__lt=day_end
            ).count()
            
            daily_stats.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': count
            })
        
        return {
            'total_logs': queryset.count(),
            'level_statistics': level_stats,
            'type_statistics': type_stats,
            'daily_statistics': daily_stats,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }
    
    @staticmethod
    def cleanup_old_logs(days: int = 30) -> int:
        """
        清理旧日志
        
        Args:
            days: 保留天数
            
        Returns:
            删除的日志数量
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        deleted_count, _ = LogEntry.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        return deleted_count


# 日志记录装饰器和辅助函数
def log_user_action(user: User, action: str, details: Optional[str] = None):
    """
    记录用户操作日志
    
    Args:
        user: 用户对象
        action: 操作名称
        details: 操作详情
    """
    message = f"用户 {user.username} 执行操作: {action}"
    if details:
        message += f" - {details}"
    
    LogService.create_log_entry(
        level='INFO',
        log_type='USER',
        message=message,
        user=user
    )


def log_system_event(level: str, message: str, module: Optional[str] = None):
    """
    记录系统事件日志
    
    Args:
        level: 日志级别
        message: 日志消息
        module: 模块名
    """
    LogService.create_log_entry(
        level=level,
        log_type='SYSTEM',
        message=message,
        module=module
    )


def log_detection_event(message: str, additional_data: Optional[Dict[str, Any]] = None):
    """
    记录检测事件日志
    
    Args:
        message: 日志消息
        additional_data: 附加数据
    """
    LogService.create_log_entry(
        level='INFO',
        log_type='DETECTION',
        message=message,
        module='detection',
        additional_data=additional_data
    )


def log_alert_event(level: str, message: str, additional_data: Optional[Dict[str, Any]] = None):
    """
    记录报警事件日志
    
    Args:
        level: 日志级别
        message: 日志消息
        additional_data: 附加数据
    """
    LogService.create_log_entry(
        level=level,
        log_type='ALERT',
        message=message,
        module='alert',
        additional_data=additional_data
    )