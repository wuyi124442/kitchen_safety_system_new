"""
异常处理和恢复机制

提供系统异常自动恢复、错误日志记录和分析功能。
实现需求 8.2 和 8.3。
"""

import time
import traceback
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ExceptionSeverity(Enum):
    """异常严重程度"""
    LOW = "low"           # 轻微异常，可自动恢复
    MEDIUM = "medium"     # 中等异常，需要重试
    HIGH = "high"         # 严重异常，需要重启模块
    CRITICAL = "critical" # 致命异常，需要系统重启


class RecoveryStrategy(Enum):
    """恢复策略"""
    RETRY = "retry"                    # 重试操作
    RESTART_MODULE = "restart_module"  # 重启模块
    RESTART_SYSTEM = "restart_system"  # 重启系统
    IGNORE = "ignore"                  # 忽略异常
    MANUAL = "manual"                  # 需要手动处理


@dataclass
class ExceptionRecord:
    """异常记录"""
    timestamp: datetime
    exception_type: str
    message: str
    traceback: str
    severity: ExceptionSeverity
    module_name: str
    recovery_strategy: RecoveryStrategy
    recovery_attempts: int = 0
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class ModuleHealth:
    """模块健康状态"""
    module_name: str
    is_healthy: bool = True
    last_error_time: Optional[datetime] = None
    error_count: int = 0
    consecutive_errors: int = 0
    recovery_attempts: int = 0
    last_recovery_time: Optional[datetime] = None
    uptime_start: datetime = field(default_factory=datetime.now)


class ExceptionHandler:
    """异常处理器"""
    
    def __init__(self, max_recovery_attempts: int = 3, 
                 recovery_cooldown: int = 60):
        """
        初始化异常处理器
        
        Args:
            max_recovery_attempts: 最大恢复尝试次数
            recovery_cooldown: 恢复冷却时间（秒）
        """
        self.max_recovery_attempts = max_recovery_attempts
        self.recovery_cooldown = recovery_cooldown
        
        # 异常记录
        self.exception_records: List[ExceptionRecord] = []
        self.module_health: Dict[str, ModuleHealth] = {}
        
        # 恢复策略映射
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'total_exceptions': 0,
            'resolved_exceptions': 0,
            'failed_recoveries': 0,
            'successful_recoveries': 0
        }
        
        logger.info("异常处理器初始化完成")
    
    def register_module(self, module_name: str, 
                       recovery_handler: Optional[Callable] = None) -> None:
        """
        注册模块
        
        Args:
            module_name: 模块名称
            recovery_handler: 恢复处理函数
        """
        with self._lock:
            self.module_health[module_name] = ModuleHealth(module_name)
            
            if recovery_handler:
                self.recovery_handlers[module_name] = recovery_handler
            
            logger.info(f"模块已注册: {module_name}")
    
    def set_recovery_strategy(self, exception_type: str, 
                            strategy: RecoveryStrategy) -> None:
        """
        设置异常恢复策略
        
        Args:
            exception_type: 异常类型
            strategy: 恢复策略
        """
        with self._lock:
            self.recovery_strategies[exception_type] = strategy
            logger.info(f"设置恢复策略: {exception_type} -> {strategy.value}")
    
    def handle_exception(self, exception: Exception, module_name: str,
                        context: Optional[Dict[str, Any]] = None) -> bool:
        """
        处理异常
        
        Args:
            exception: 异常对象
            module_name: 发生异常的模块名称
            context: 异常上下文信息
            
        Returns:
            是否成功处理异常
        """
        with self._lock:
            # 创建异常记录
            exception_record = self._create_exception_record(
                exception, module_name, context
            )
            
            # 更新模块健康状态
            self._update_module_health(module_name, exception_record)
            
            # 记录异常
            self.exception_records.append(exception_record)
            self.stats['total_exceptions'] += 1
            
            # 记录日志
            self._log_exception(exception_record)
            
            # 尝试恢复
            recovery_success = self._attempt_recovery(exception_record)
            
            if recovery_success:
                self.stats['successful_recoveries'] += 1
                exception_record.resolved = True
                exception_record.resolution_time = datetime.now()
                self.stats['resolved_exceptions'] += 1
            else:
                self.stats['failed_recoveries'] += 1
            
            return recovery_success
    
    def _create_exception_record(self, exception: Exception, module_name: str,
                               context: Optional[Dict[str, Any]] = None) -> ExceptionRecord:
        """创建异常记录"""
        exception_type = type(exception).__name__
        severity = self._determine_severity(exception, module_name)
        strategy = self._get_recovery_strategy(exception_type, severity)
        
        return ExceptionRecord(
            timestamp=datetime.now(),
            exception_type=exception_type,
            message=str(exception),
            traceback=traceback.format_exc(),
            severity=severity,
            module_name=module_name,
            recovery_strategy=strategy
        )
    
    def _determine_severity(self, exception: Exception, 
                          module_name: str) -> ExceptionSeverity:
        """确定异常严重程度"""
        exception_type = type(exception).__name__
        
        # 根据异常类型确定严重程度
        if exception_type in ['ConnectionError', 'TimeoutError', 'IOError']:
            return ExceptionSeverity.MEDIUM
        elif exception_type in ['MemoryError', 'SystemError']:
            return ExceptionSeverity.CRITICAL
        elif exception_type in ['ValueError', 'TypeError', 'AttributeError']:
            return ExceptionSeverity.LOW
        elif exception_type in ['RuntimeError', 'OSError']:
            return ExceptionSeverity.HIGH
        else:
            return ExceptionSeverity.MEDIUM
    
    def _get_recovery_strategy(self, exception_type: str, 
                             severity: ExceptionSeverity) -> RecoveryStrategy:
        """获取恢复策略"""
        # 优先使用配置的策略
        if exception_type in self.recovery_strategies:
            return self.recovery_strategies[exception_type]
        
        # 根据严重程度确定默认策略
        if severity == ExceptionSeverity.LOW:
            return RecoveryStrategy.RETRY
        elif severity == ExceptionSeverity.MEDIUM:
            return RecoveryStrategy.RESTART_MODULE
        elif severity == ExceptionSeverity.HIGH:
            return RecoveryStrategy.RESTART_MODULE
        else:  # CRITICAL
            return RecoveryStrategy.RESTART_SYSTEM
    
    def _update_module_health(self, module_name: str, 
                            exception_record: ExceptionRecord) -> None:
        """更新模块健康状态"""
        if module_name not in self.module_health:
            self.module_health[module_name] = ModuleHealth(module_name)
        
        health = self.module_health[module_name]
        health.last_error_time = exception_record.timestamp
        health.error_count += 1
        health.consecutive_errors += 1
        health.is_healthy = False
    
    def _log_exception(self, record: ExceptionRecord) -> None:
        """记录异常日志"""
        logger.error(
            f"异常发生 - 模块: {record.module_name}, "
            f"类型: {record.exception_type}, "
            f"严重程度: {record.severity.value}, "
            f"恢复策略: {record.recovery_strategy.value}, "
            f"消息: {record.message}"
        )
        
        # 详细的异常信息记录到DEBUG级别
        logger.debug(f"异常堆栈:\n{record.traceback}")
    
    def _attempt_recovery(self, record: ExceptionRecord) -> bool:
        """尝试恢复"""
        module_name = record.module_name
        strategy = record.recovery_strategy
        
        # 检查是否超过最大恢复尝试次数
        health = self.module_health.get(module_name)
        if health and health.recovery_attempts >= self.max_recovery_attempts:
            logger.error(f"模块 {module_name} 恢复尝试次数已达上限")
            return False
        
        # 检查恢复冷却时间
        if health and health.last_recovery_time:
            time_since_last = datetime.now() - health.last_recovery_time
            if time_since_last.total_seconds() < self.recovery_cooldown:
                logger.warning(f"模块 {module_name} 仍在恢复冷却期内")
                return False
        
        logger.info(f"尝试恢复模块 {module_name}，策略: {strategy.value}")
        
        try:
            success = False
            
            if strategy == RecoveryStrategy.RETRY:
                success = self._retry_operation(record)
            elif strategy == RecoveryStrategy.RESTART_MODULE:
                success = self._restart_module(record)
            elif strategy == RecoveryStrategy.RESTART_SYSTEM:
                success = self._restart_system(record)
            elif strategy == RecoveryStrategy.IGNORE:
                success = True  # 忽略异常
            else:  # MANUAL
                logger.warning(f"异常需要手动处理: {record.exception_type}")
                success = False
            
            if health:
                health.recovery_attempts += 1
                health.last_recovery_time = datetime.now()
                
                if success:
                    health.consecutive_errors = 0
                    health.is_healthy = True
                    logger.info(f"模块 {module_name} 恢复成功")
                else:
                    logger.error(f"模块 {module_name} 恢复失败")
            
            return success
            
        except Exception as e:
            logger.error(f"恢复过程中发生异常: {e}")
            return False
    
    def _retry_operation(self, record: ExceptionRecord) -> bool:
        """重试操作"""
        # 简单的重试策略，等待一段时间
        time.sleep(1.0)
        return True
    
    def _restart_module(self, record: ExceptionRecord) -> bool:
        """重启模块"""
        module_name = record.module_name
        
        if module_name in self.recovery_handlers:
            try:
                handler = self.recovery_handlers[module_name]
                return handler()
            except Exception as e:
                logger.error(f"模块重启处理器执行失败: {e}")
                return False
        else:
            logger.warning(f"模块 {module_name} 没有注册恢复处理器")
            return False
    
    def _restart_system(self, record: ExceptionRecord) -> bool:
        """重启系统"""
        logger.critical("系统需要重启以恢复正常运行")
        # 这里可以触发系统重启逻辑
        return False
    
    def get_module_health(self, module_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取模块健康状态
        
        Args:
            module_name: 模块名称，None表示获取所有模块
            
        Returns:
            模块健康状态信息
        """
        with self._lock:
            if module_name:
                if module_name in self.module_health:
                    health = self.module_health[module_name]
                    return {
                        'module_name': health.module_name,
                        'is_healthy': health.is_healthy,
                        'error_count': health.error_count,
                        'consecutive_errors': health.consecutive_errors,
                        'recovery_attempts': health.recovery_attempts,
                        'uptime_seconds': (datetime.now() - health.uptime_start).total_seconds(),
                        'last_error_time': health.last_error_time.isoformat() if health.last_error_time else None,
                        'last_recovery_time': health.last_recovery_time.isoformat() if health.last_recovery_time else None
                    }
                else:
                    return {}
            else:
                return {
                    name: {
                        'module_name': health.module_name,
                        'is_healthy': health.is_healthy,
                        'error_count': health.error_count,
                        'consecutive_errors': health.consecutive_errors,
                        'recovery_attempts': health.recovery_attempts,
                        'uptime_seconds': (datetime.now() - health.uptime_start).total_seconds(),
                        'last_error_time': health.last_error_time.isoformat() if health.last_error_time else None,
                        'last_recovery_time': health.last_recovery_time.isoformat() if health.last_recovery_time else None
                    }
                    for name, health in self.module_health.items()
                }
    
    def get_exception_statistics(self) -> Dict[str, Any]:
        """获取异常统计信息"""
        with self._lock:
            recent_exceptions = [
                record for record in self.exception_records
                if (datetime.now() - record.timestamp).total_seconds() < 3600  # 最近1小时
            ]
            
            return {
                'total_exceptions': self.stats['total_exceptions'],
                'resolved_exceptions': self.stats['resolved_exceptions'],
                'failed_recoveries': self.stats['failed_recoveries'],
                'successful_recoveries': self.stats['successful_recoveries'],
                'recent_exceptions_count': len(recent_exceptions),
                'resolution_rate': (
                    self.stats['resolved_exceptions'] / max(1, self.stats['total_exceptions'])
                ),
                'recovery_success_rate': (
                    self.stats['successful_recoveries'] / 
                    max(1, self.stats['successful_recoveries'] + self.stats['failed_recoveries'])
                )
            }
    
    def get_recent_exceptions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取最近的异常记录
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            异常记录列表
        """
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_records = [
                record for record in self.exception_records
                if record.timestamp >= cutoff_time
            ]
            
            return [
                {
                    'timestamp': record.timestamp.isoformat(),
                    'exception_type': record.exception_type,
                    'message': record.message,
                    'severity': record.severity.value,
                    'module_name': record.module_name,
                    'recovery_strategy': record.recovery_strategy.value,
                    'recovery_attempts': record.recovery_attempts,
                    'resolved': record.resolved,
                    'resolution_time': record.resolution_time.isoformat() if record.resolution_time else None
                }
                for record in recent_records
            ]
    
    def cleanup_old_records(self, days: int = 7) -> None:
        """
        清理旧的异常记录
        
        Args:
            days: 保留天数
        """
        with self._lock:
            cutoff_time = datetime.now() - timedelta(days=days)
            old_count = len(self.exception_records)
            
            self.exception_records = [
                record for record in self.exception_records
                if record.timestamp >= cutoff_time
            ]
            
            new_count = len(self.exception_records)
            logger.info(f"清理了 {old_count - new_count} 条旧异常记录")


# 全局异常处理器实例
exception_handler = ExceptionHandler()