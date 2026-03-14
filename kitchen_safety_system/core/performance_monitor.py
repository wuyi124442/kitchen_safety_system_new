"""
性能监控和优化系统

提供CPU和内存使用率监控、检测速度优化功能。
实现需求 8.4 和 8.5。
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceLevel(Enum):
    """性能级别"""
    EXCELLENT = "excellent"  # 优秀 (< 50% CPU, < 50% Memory)
    GOOD = "good"           # 良好 (< 70% CPU, < 60% Memory)
    WARNING = "warning"     # 警告 (< 80% CPU, < 70% Memory)
    CRITICAL = "critical"   # 严重 (>= 80% CPU, >= 70% Memory)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    fps: float
    frame_processing_time: float
    detection_time: float
    pose_analysis_time: float
    total_processing_time: float
    queue_sizes: Dict[str, int] = field(default_factory=dict)
    thread_count: int = 0
    gpu_usage: Optional[float] = None
    gpu_memory_used: Optional[float] = None


@dataclass
class PerformanceAlert:
    """性能警报"""
    timestamp: datetime
    alert_type: str
    message: str
    level: PerformanceLevel
    metrics: PerformanceMetrics
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, monitoring_interval: float = 1.0,
                 history_size: int = 3600):
        """
        初始化性能监控器
        
        Args:
            monitoring_interval: 监控间隔（秒）
            history_size: 历史数据保存数量
        """
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size
        
        # 性能数据
        self.metrics_history: deque = deque(maxlen=history_size)
        self.alerts: List[PerformanceAlert] = []
        
        # 监控线程
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_monitoring = False
        
        # 性能阈值
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 80.0,
            'memory_warning': 60.0,
            'memory_critical': 70.0,
            'fps_warning': 10.0,
            'fps_critical': 5.0,
            'processing_time_warning': 100.0,  # ms
            'processing_time_critical': 200.0  # ms
        }
        
        # 性能优化回调
        self.optimization_callbacks: Dict[str, Callable] = {}
        
        # 统计信息
        self.stats = {
            'monitoring_start_time': None,
            'total_alerts': 0,
            'resolved_alerts': 0,
            'optimization_triggers': 0
        }
        
        # 线程锁
        self._lock = threading.RLock()
        
        logger.info("性能监控器初始化完成")
    
    def set_threshold(self, metric: str, value: float) -> None:
        """
        设置性能阈值
        
        Args:
            metric: 指标名称
            value: 阈值
        """
        with self._lock:
            self.thresholds[metric] = value
            logger.info(f"设置性能阈值: {metric} = {value}")
    
    def register_optimization_callback(self, alert_type: str, 
                                     callback: Callable) -> None:
        """
        注册性能优化回调
        
        Args:
            alert_type: 警报类型
            callback: 优化回调函数
        """
        with self._lock:
            self.optimization_callbacks[alert_type] = callback
            logger.info(f"注册优化回调: {alert_type}")
    
    def start_monitoring(self) -> bool:
        """
        开始性能监控
        
        Returns:
            是否启动成功
        """
        if self.is_monitoring:
            logger.warning("性能监控已在运行")
            return True
        
        try:
            self.is_monitoring = True
            self.stats['monitoring_start_time'] = datetime.now()
            
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
            logger.info("性能监控已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动性能监控失败: {e}")
            self.is_monitoring = False
            return False
    
    def stop_monitoring(self) -> None:
        """停止性能监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        
        logger.info("性能监控已停止")
    
    def _monitoring_loop(self) -> None:
        """监控循环"""
        logger.info("性能监控循环开始")
        
        while self.is_monitoring:
            try:
                # 收集性能指标
                metrics = self._collect_metrics()
                
                # 保存到历史记录
                with self._lock:
                    self.metrics_history.append(metrics)
                
                # 检查性能警报
                self._check_performance_alerts(metrics)
                
                # 等待下次监控
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"性能监控循环异常: {e}")
                time.sleep(self.monitoring_interval)
        
        logger.info("性能监控循环结束")
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # 系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # 进程信息
        process = psutil.Process()
        thread_count = process.num_threads()
        
        # GPU使用情况（如果可用）
        gpu_usage = None
        gpu_memory_used = None
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_usage = gpu.load * 100
                gpu_memory_used = gpu.memoryUsed
        except ImportError:
            pass  # GPU监控不可用
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            fps=0.0,  # 将由外部更新
            frame_processing_time=0.0,  # 将由外部更新
            detection_time=0.0,  # 将由外部更新
            pose_analysis_time=0.0,  # 将由外部更新
            total_processing_time=0.0,  # 将由外部更新
            thread_count=thread_count,
            gpu_usage=gpu_usage,
            gpu_memory_used=gpu_memory_used
        )
    
    def update_processing_metrics(self, fps: float = 0.0,
                                frame_processing_time: float = 0.0,
                                detection_time: float = 0.0,
                                pose_analysis_time: float = 0.0,
                                queue_sizes: Optional[Dict[str, int]] = None) -> None:
        """
        更新处理性能指标
        
        Args:
            fps: 帧率
            frame_processing_time: 帧处理时间（毫秒）
            detection_time: 检测时间（毫秒）
            pose_analysis_time: 姿态分析时间（毫秒）
            queue_sizes: 队列大小
        """
        with self._lock:
            if self.metrics_history:
                latest_metrics = self.metrics_history[-1]
                latest_metrics.fps = fps
                latest_metrics.frame_processing_time = frame_processing_time
                latest_metrics.detection_time = detection_time
                latest_metrics.pose_analysis_time = pose_analysis_time
                latest_metrics.total_processing_time = (
                    frame_processing_time + detection_time + pose_analysis_time
                )
                
                if queue_sizes:
                    latest_metrics.queue_sizes = queue_sizes.copy()
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics) -> None:
        """检查性能警报"""
        alerts_to_create = []
        
        # CPU使用率检查
        if metrics.cpu_percent >= self.thresholds['cpu_critical']:
            alerts_to_create.append(
                ('cpu_critical', f"CPU使用率过高: {metrics.cpu_percent:.1f}%", 
                 PerformanceLevel.CRITICAL)
            )
        elif metrics.cpu_percent >= self.thresholds['cpu_warning']:
            alerts_to_create.append(
                ('cpu_warning', f"CPU使用率警告: {metrics.cpu_percent:.1f}%", 
                 PerformanceLevel.WARNING)
            )
        
        # 内存使用率检查
        if metrics.memory_percent >= self.thresholds['memory_critical']:
            alerts_to_create.append(
                ('memory_critical', f"内存使用率过高: {metrics.memory_percent:.1f}%", 
                 PerformanceLevel.CRITICAL)
            )
        elif metrics.memory_percent >= self.thresholds['memory_warning']:
            alerts_to_create.append(
                ('memory_warning', f"内存使用率警告: {metrics.memory_percent:.1f}%", 
                 PerformanceLevel.WARNING)
            )
        
        # FPS检查
        if metrics.fps > 0:
            if metrics.fps <= self.thresholds['fps_critical']:
                alerts_to_create.append(
                    ('fps_critical', f"帧率过低: {metrics.fps:.1f} FPS", 
                     PerformanceLevel.CRITICAL)
                )
            elif metrics.fps <= self.thresholds['fps_warning']:
                alerts_to_create.append(
                    ('fps_warning', f"帧率警告: {metrics.fps:.1f} FPS", 
                     PerformanceLevel.WARNING)
                )
        
        # 处理时间检查
        if metrics.total_processing_time >= self.thresholds['processing_time_critical']:
            alerts_to_create.append(
                ('processing_time_critical', 
                 f"处理时间过长: {metrics.total_processing_time:.1f}ms", 
                 PerformanceLevel.CRITICAL)
            )
        elif metrics.total_processing_time >= self.thresholds['processing_time_warning']:
            alerts_to_create.append(
                ('processing_time_warning', 
                 f"处理时间警告: {metrics.total_processing_time:.1f}ms", 
                 PerformanceLevel.WARNING)
            )
        
        # 创建警报
        for alert_type, message, level in alerts_to_create:
            self._create_alert(alert_type, message, level, metrics)
    
    def _create_alert(self, alert_type: str, message: str, 
                     level: PerformanceLevel, metrics: PerformanceMetrics) -> None:
        """创建性能警报"""
        with self._lock:
            # 检查是否已有相同类型的未解决警报
            existing_alert = None
            for alert in reversed(self.alerts):
                if alert.alert_type == alert_type and not alert.resolved:
                    existing_alert = alert
                    break
            
            if existing_alert:
                # 更新现有警报的时间戳
                existing_alert.timestamp = datetime.now()
                existing_alert.metrics = metrics
            else:
                # 创建新警报
                alert = PerformanceAlert(
                    timestamp=datetime.now(),
                    alert_type=alert_type,
                    message=message,
                    level=level,
                    metrics=metrics
                )
                
                self.alerts.append(alert)
                self.stats['total_alerts'] += 1
                
                # 记录日志
                logger.warning(f"性能警报: {message}")
                
                # 触发优化回调
                self._trigger_optimization(alert_type, alert)
    
    def _trigger_optimization(self, alert_type: str, alert: PerformanceAlert) -> None:
        """触发性能优化"""
        if alert_type in self.optimization_callbacks:
            try:
                callback = self.optimization_callbacks[alert_type]
                callback(alert)
                self.stats['optimization_triggers'] += 1
                logger.info(f"触发性能优化: {alert_type}")
            except Exception as e:
                logger.error(f"性能优化回调执行失败: {e}")
    
    def resolve_alert(self, alert_type: str) -> bool:
        """
        解决性能警报
        
        Args:
            alert_type: 警报类型
            
        Returns:
            是否成功解决
        """
        with self._lock:
            resolved_count = 0
            
            for alert in reversed(self.alerts):
                if alert.alert_type == alert_type and not alert.resolved:
                    alert.resolved = True
                    alert.resolution_time = datetime.now()
                    resolved_count += 1
                    self.stats['resolved_alerts'] += 1
            
            if resolved_count > 0:
                logger.info(f"解决了 {resolved_count} 个 {alert_type} 警报")
                return True
            
            return False
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        with self._lock:
            if self.metrics_history:
                return self.metrics_history[-1]
            return None
    
    def get_performance_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Args:
            minutes: 统计时间范围（分钟）
            
        Returns:
            性能摘要信息
        """
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_metrics = [
                m for m in self.metrics_history
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            # 计算统计信息
            cpu_values = [m.cpu_percent for m in recent_metrics]
            memory_values = [m.memory_percent for m in recent_metrics]
            fps_values = [m.fps for m in recent_metrics if m.fps > 0]
            processing_times = [m.total_processing_time for m in recent_metrics if m.total_processing_time > 0]
            
            current_metrics = recent_metrics[-1]
            
            return {
                'current': {
                    'cpu_percent': current_metrics.cpu_percent,
                    'memory_percent': current_metrics.memory_percent,
                    'memory_used_mb': current_metrics.memory_used_mb,
                    'fps': current_metrics.fps,
                    'processing_time_ms': current_metrics.total_processing_time,
                    'thread_count': current_metrics.thread_count,
                    'gpu_usage': current_metrics.gpu_usage,
                    'gpu_memory_used': current_metrics.gpu_memory_used
                },
                'averages': {
                    'cpu_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    'memory_percent': sum(memory_values) / len(memory_values) if memory_values else 0,
                    'fps': sum(fps_values) / len(fps_values) if fps_values else 0,
                    'processing_time_ms': sum(processing_times) / len(processing_times) if processing_times else 0
                },
                'peaks': {
                    'max_cpu_percent': max(cpu_values) if cpu_values else 0,
                    'max_memory_percent': max(memory_values) if memory_values else 0,
                    'min_fps': min(fps_values) if fps_values else 0,
                    'max_processing_time_ms': max(processing_times) if processing_times else 0
                },
                'performance_level': self._get_performance_level(current_metrics),
                'data_points': len(recent_metrics),
                'time_range_minutes': minutes
            }
    
    def _get_performance_level(self, metrics: PerformanceMetrics) -> str:
        """获取性能级别"""
        if (metrics.cpu_percent >= self.thresholds['cpu_critical'] or 
            metrics.memory_percent >= self.thresholds['memory_critical']):
            return PerformanceLevel.CRITICAL.value
        elif (metrics.cpu_percent >= self.thresholds['cpu_warning'] or 
              metrics.memory_percent >= self.thresholds['memory_warning']):
            return PerformanceLevel.WARNING.value
        elif (metrics.cpu_percent < 50 and metrics.memory_percent < 50):
            return PerformanceLevel.EXCELLENT.value
        else:
            return PerformanceLevel.GOOD.value
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃的性能警报"""
        with self._lock:
            active_alerts = [alert for alert in self.alerts if not alert.resolved]
            
            return [
                {
                    'timestamp': alert.timestamp.isoformat(),
                    'alert_type': alert.alert_type,
                    'message': alert.message,
                    'level': alert.level.value,
                    'cpu_percent': alert.metrics.cpu_percent,
                    'memory_percent': alert.metrics.memory_percent,
                    'fps': alert.metrics.fps,
                    'processing_time_ms': alert.metrics.total_processing_time
                }
                for alert in active_alerts
            ]
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        with self._lock:
            uptime = 0
            if self.stats['monitoring_start_time']:
                uptime = (datetime.now() - self.stats['monitoring_start_time']).total_seconds()
            
            return {
                'monitoring_uptime_seconds': uptime,
                'total_alerts': self.stats['total_alerts'],
                'resolved_alerts': self.stats['resolved_alerts'],
                'active_alerts': len([a for a in self.alerts if not a.resolved]),
                'optimization_triggers': self.stats['optimization_triggers'],
                'metrics_collected': len(self.metrics_history),
                'is_monitoring': self.is_monitoring,
                'thresholds': self.thresholds.copy()
            }
    
    def cleanup_old_data(self, hours: int = 24) -> None:
        """
        清理旧数据
        
        Args:
            hours: 保留小时数
        """
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 清理旧警报
            old_alert_count = len(self.alerts)
            self.alerts = [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff_time
            ]
            new_alert_count = len(self.alerts)
            
            logger.info(f"清理了 {old_alert_count - new_alert_count} 条旧性能警报")


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()