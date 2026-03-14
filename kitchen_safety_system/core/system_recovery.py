"""
系统恢复管理器

协调整个系统的异常恢复和健康监控。
实现需求 8.2 和 8.3。
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ..utils.logger import get_logger
from .exception_handler import exception_handler, ExceptionSeverity
from .performance_monitor import performance_monitor, PerformanceLevel

logger = get_logger(__name__)


class SystemHealth(Enum):
    """系统健康状态"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


@dataclass
class SystemStatus:
    """系统状态信息"""
    overall_health: SystemHealth
    module_health: Dict[str, bool]
    performance_level: PerformanceLevel
    uptime_seconds: float
    last_recovery_time: Optional[datetime]
    recovery_count: int
    active_alerts: int
    error_rate: float


class SystemRecoveryManager:
    """系统恢复管理器"""
    
    def __init__(self, health_check_interval: float = 30.0):
        """
        初始化系统恢复管理器
        
        Args:
            health_check_interval: 健康检查间隔（秒）
        """
        self.health_check_interval = health_check_interval
        self.start_time = datetime.now()
        self.last_recovery_time: Optional[datetime] = None
        self.recovery_count = 0
        
        # 监控线程
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_monitoring = False
        
        # 注册的模块
        self.registered_modules: Dict[str, Callable] = {}
        
        # 健康检查回调
        self.health_callbacks: List[Callable] = []
        
        # 线程锁
        self._lock = threading.RLock()
        
        logger.info("系统恢复管理器初始化完成")
    
    def register_module(self, module_name: str, health_check: Callable[[], bool]) -> None:
        """
        注册模块健康检查
        
        Args:
            module_name: 模块名称
            health_check: 健康检查函数
        """
        with self._lock:
            self.registered_modules[module_name] = health_check
            logger.info(f"模块已注册健康检查: {module_name}")
    
    def register_health_callback(self, callback: Callable[[SystemStatus], None]) -> None:
        """
        注册健康状态回调
        
        Args:
            callback: 健康状态变化回调函数
        """
        with self._lock:
            self.health_callbacks.append(callback)
            logger.info("健康状态回调已注册")
    
    def start_monitoring(self) -> bool:
        """
        开始系统健康监控
        
        Returns:
            是否启动成功
        """
        if self.is_monitoring:
            logger.warning("系统健康监控已在运行")
            return True
        
        try:
            self.is_monitoring = True
            
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
            logger.info("系统健康监控已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动系统健康监控失败: {e}")
            self.is_monitoring = False
            return False
    
    def stop_monitoring(self) -> None:
        """停止系统健康监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        
        logger.info("系统健康监控已停止")
    
    def _monitoring_loop(self) -> None:
        """健康监控循环"""
        logger.info("系统健康监控循环开始")
        
        while self.is_monitoring:
            try:
                # 执行健康检查
                system_status = self.check_system_health()
                
                # 根据健康状态采取行动
                self._handle_health_status(system_status)
                
                # 通知回调
                for callback in self.health_callbacks:
                    try:
                        callback(system_status)
                    except Exception as e:
                        logger.error(f"健康状态回调执行失败: {e}")
                
                # 等待下次检查
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"健康监控循环异常: {e}")
                time.sleep(self.health_check_interval)
        
        logger.info("系统健康监控循环结束")
    
    def check_system_health(self) -> SystemStatus:
        """
        检查系统健康状态
        
        Returns:
            系统状态信息
        """
        with self._lock:
            # 检查模块健康状态
            module_health = {}
            healthy_modules = 0
            
            for module_name, health_check in self.registered_modules.items():
                try:
                    is_healthy = health_check()
                    module_health[module_name] = is_healthy
                    if is_healthy:
                        healthy_modules += 1
                except Exception as e:
                    logger.error(f"模块 {module_name} 健康检查失败: {e}")
                    module_health[module_name] = False
            
            # 获取异常处理状态
            exception_stats = exception_handler.get_exception_statistics()
            
            # 获取性能监控状态
            performance_summary = performance_monitor.get_performance_summary(minutes=5)
            active_alerts = performance_monitor.get_active_alerts()
            
            # 计算整体健康状态
            total_modules = len(self.registered_modules)
            health_ratio = healthy_modules / max(1, total_modules)
            
            if health_ratio >= 0.9 and len(active_alerts) == 0:
                overall_health = SystemHealth.HEALTHY
            elif health_ratio >= 0.7 and len(active_alerts) <= 2:
                overall_health = SystemHealth.WARNING
            elif health_ratio >= 0.5:
                overall_health = SystemHealth.CRITICAL
            else:
                overall_health = SystemHealth.FAILED
            
            # 计算错误率
            error_rate = 0.0
            if exception_stats['total_exceptions'] > 0:
                error_rate = (
                    exception_stats['total_exceptions'] - exception_stats['resolved_exceptions']
                ) / exception_stats['total_exceptions']
            
            # 获取性能级别
            performance_level = PerformanceLevel.GOOD
            if performance_summary and 'performance_level' in performance_summary:
                level_str = performance_summary['performance_level']
                try:
                    performance_level = PerformanceLevel(level_str)
                except ValueError:
                    performance_level = PerformanceLevel.GOOD
            
            return SystemStatus(
                overall_health=overall_health,
                module_health=module_health,
                performance_level=performance_level,
                uptime_seconds=(datetime.now() - self.start_time).total_seconds(),
                last_recovery_time=self.last_recovery_time,
                recovery_count=self.recovery_count,
                active_alerts=len(active_alerts),
                error_rate=error_rate
            )
    
    def _handle_health_status(self, status: SystemStatus) -> None:
        """
        处理健康状态
        
        Args:
            status: 系统状态
        """
        if status.overall_health == SystemHealth.FAILED:
            logger.critical("系统健康状态严重，尝试全系统恢复")
            self._trigger_system_recovery()
        elif status.overall_health == SystemHealth.CRITICAL:
            logger.error("系统健康状态危险，尝试模块恢复")
            self._trigger_module_recovery(status.module_health)
        elif status.overall_health == SystemHealth.WARNING:
            logger.warning(f"系统健康状态警告，活跃警报: {status.active_alerts}")
            # 记录性能警告（需求 8.3）
            if status.performance_level in [PerformanceLevel.WARNING, PerformanceLevel.CRITICAL]:
                logger.warning(f"系统资源使用过高: {status.performance_level.value}")
    
    def _trigger_system_recovery(self) -> bool:
        """
        触发全系统恢复
        
        Returns:
            是否恢复成功
        """
        try:
            logger.info("开始全系统恢复...")
            self.recovery_count += 1
            self.last_recovery_time = datetime.now()
            
            # 停止性能监控
            performance_monitor.stop_monitoring()
            
            # 清理异常记录
            exception_handler.cleanup_old_records(days=1)
            
            # 清理性能数据
            performance_monitor.cleanup_old_data(hours=1)
            
            # 重启性能监控
            performance_monitor.start_monitoring()
            
            logger.info("全系统恢复完成")
            return True
            
        except Exception as e:
            logger.error(f"全系统恢复失败: {e}")
            return False
    
    def _trigger_module_recovery(self, module_health: Dict[str, bool]) -> None:
        """
        触发模块恢复
        
        Args:
            module_health: 模块健康状态
        """
        for module_name, is_healthy in module_health.items():
            if not is_healthy:
                logger.warning(f"模块 {module_name} 不健康，尝试恢复")
                # 异常处理器会自动尝试恢复
                # 这里只是记录日志
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态信息
        
        Returns:
            系统状态字典
        """
        status = self.check_system_health()
        
        return {
            'overall_health': status.overall_health.value,
            'module_health': status.module_health,
            'performance_level': status.performance_level.value,
            'uptime_seconds': status.uptime_seconds,
            'uptime_hours': status.uptime_seconds / 3600,
            'last_recovery_time': status.last_recovery_time.isoformat() if status.last_recovery_time else None,
            'recovery_count': status.recovery_count,
            'active_alerts': status.active_alerts,
            'error_rate': status.error_rate,
            'is_monitoring': self.is_monitoring,
            'registered_modules': list(self.registered_modules.keys())
        }
    
    def force_recovery(self) -> bool:
        """
        强制执行系统恢复
        
        Returns:
            是否恢复成功
        """
        logger.info("强制执行系统恢复")
        return self._trigger_system_recovery()


# 全局系统恢复管理器实例
system_recovery_manager = SystemRecoveryManager()