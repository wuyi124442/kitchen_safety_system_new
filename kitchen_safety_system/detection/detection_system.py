"""
主检测系统控制器

协调各个模块的工作流程，实现系统启动和关闭管理。
"""

import time
import threading
from typing import List, Dict, Any, Optional
import numpy as np
from queue import Queue, Empty
import traceback

from ..core.interfaces import (
    IDetectionSystem, IVideoCapture, IVideoProcessor, IObjectDetector,
    IPoseAnalyzer, IRiskMonitor, IAlertManager, DetectionResult, 
    AlertEvent, PoseResult, BoundingBox, DetectionType
)
from ..core.models import SystemStatus, SystemConfig
from ..core.config import config_manager
from ..video.video_capture import VideoCapture
from ..video.video_processor import VideoProcessor
from ..detection.yolo_detector import YOLODetector
from ..pose.pose_analyzer import PoseAnalyzer
from ..risk.stove_monitor import StoveMonitor
from ..risk.risk_assessment import RiskAssessment
from ..alerts.alert_manager import AlertManager
from ..utils.logger import get_logger
from ..core.exception_handler import exception_handler
from ..core.performance_monitor import performance_monitor
from ..core.system_recovery import system_recovery_manager

logger = get_logger(__name__)


class DetectionSystem(IDetectionSystem):
    """主检测系统控制器"""
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """
        初始化检测系统
        
        Args:
            config: 系统配置，如果为None则使用默认配置
        """
        self.config = config or SystemConfig()
        self.logger = get_logger(__name__)
        
        # 系统状态
        self.is_initialized = False
        self.is_running = False
        self.start_time = None
        self.frame_count = 0
        self.error_count = 0
        
        # 核心组件
        self.video_capture: Optional[IVideoCapture] = None
        self.video_processor: Optional[IVideoProcessor] = None
        self.object_detector: Optional[IObjectDetector] = None
        self.pose_analyzer: Optional[IPoseAnalyzer] = None
        self.risk_monitor: Optional[IRiskMonitor] = None
        self.alert_manager: Optional[IAlertManager] = None
        
        # 处理线程和队列
        self.processing_thread: Optional[threading.Thread] = None
        self.frame_queue: Queue = Queue(maxsize=10)
        self.result_queue: Queue = Queue(maxsize=100)
        
        # 性能监控
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        # 异常处理
        self.max_consecutive_errors = 5
        self.consecutive_errors = 0
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
        # 性能监控
        self.processing_times = {
            'detection': 0.0,
            'pose_analysis': 0.0,
            'risk_assessment': 0.0,
            'total': 0.0
        }
        
        # 注册异常处理和性能监控
        self._setup_exception_handling()
        self._setup_performance_monitoring()
    
    def initialize(self) -> bool:
        """
        初始化系统所有组件
        
        Returns:
            是否初始化成功
        """
        try:
            self.logger.info("开始初始化检测系统...")
            
            # 初始化视频采集器
            video_source = self.config.video_input_source
            target_fps = self.config.detection_fps
            self.video_capture = VideoCapture(video_source, target_fps)
            
            # 初始化视频处理器
            self.video_processor = VideoProcessor(
                target_format="BGR",
                target_resolution=self.config.video_resolution,
                quality_threshold=0.5
            )
            
            # 初始化YOLO检测器
            self.object_detector = YOLODetector(
                model_path="yolo/yolo11n.pt",
                confidence_threshold=self.config.confidence_threshold,
                device="cpu"
            )
            
            # 初始化姿态分析器
            self.pose_analyzer = PoseAnalyzer(
                confidence_threshold=self.config.fall_confidence_threshold,
                fall_angle_threshold=45.0,
                fall_height_ratio_threshold=0.6
            )
            
            # 初始化风险监控器
            self.risk_monitor = StoveMonitor(
                distance_threshold=self.config.stove_distance_threshold,
                unattended_time_threshold=self.config.unattended_time_threshold
            )
            
            # 初始化报警管理器
            self.alert_manager = AlertManager(self.config)
            
            self.is_initialized = True
            self.logger.info("检测系统初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"检测系统初始化失败: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def start_detection(self) -> bool:
        """
        启动检测系统
        
        Returns:
            是否启动成功
        """
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        try:
            self.logger.info("启动检测系统...")
            
            # 启动视频采集
            if not self.video_capture.start_capture():
                self.logger.error("视频采集启动失败")
                return False
            
            # 重置状态
            self.is_running = True
            self.start_time = time.time()
            self.frame_count = 0
            self.error_count = 0
            self.consecutive_errors = 0
            self.recovery_attempts = 0
            
            # 启动处理线程
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True
            )
            self.processing_thread.start()
            
            self.logger.info("检测系统启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"检测系统启动失败: {e}")
            self.logger.error(traceback.format_exc())
            self.is_running = False
            return False
    
    def stop_detection(self) -> None:
        """停止检测系统"""
        try:
            self.logger.info("停止检测系统...")
            
            # 停止处理循环
            self.is_running = False
            
            # 等待处理线程结束
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5.0)
            
            # 停止视频采集
            if self.video_capture:
                self.video_capture.stop_capture()
            
            # 清空队列
            self._clear_queues()
            
            self.logger.info("检测系统已停止")
            
        except Exception as e:
            self.logger.error(f"停止检测系统时发生错误: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态信息
        
        Returns:
            系统状态字典
        """
        uptime = time.time() - self.start_time if self.start_time else 0
        
        status = {
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'uptime_seconds': uptime,
            'frame_count': self.frame_count,
            'error_count': self.error_count,
            'current_fps': self.current_fps,
            'consecutive_errors': self.consecutive_errors,
            'recovery_attempts': self.recovery_attempts,
            'video_connected': self.video_capture.is_connected() if self.video_capture else False,
            'queue_sizes': {
                'frame_queue': self.frame_queue.qsize(),
                'result_queue': self.result_queue.qsize()
            }
        }
        
        return status
    
    def process_frame_pipeline(self, frame: np.ndarray) -> List[AlertEvent]:
        """
        处理单帧的完整流水线
        
        Args:
            frame: 输入视频帧
            
        Returns:
            检测到的报警事件列表
        """
        alerts = []
        
        try:
            # 1. 视频预处理
            processed_frame = self.video_processor.process_frame(frame)
            
            # 2. 目标检测
            detections = self.object_detector.detect(processed_frame)
            
            # 3. 姿态分析（针对检测到的人员）
            pose_results = []
            for detection in detections:
                if detection.detection_type == DetectionType.PERSON:
                    pose_result = self.pose_analyzer.analyze_pose(
                        processed_frame, detection.bbox
                    )
                    pose_results.append(pose_result)
                    
                    # 检查跌倒
                    if pose_result.is_fall_detected:
                        fall_alert = AlertEvent(
                            alert_type="fall_detected",
                            alert_level="high",
                            timestamp=time.time(),
                            location=detection.bbox.center,
                            description=f"检测到人员跌倒，置信度: {pose_result.fall_confidence:.2f}"
                        )
                        alerts.append(fall_alert)
            
            # 4. 风险监控（灶台安全）
            stove_alert = self.risk_monitor.monitor_stove_safety(detections)
            if stove_alert:
                alerts.append(stove_alert)
            
            # 5. 触发报警
            for alert in alerts:
                self.alert_manager.trigger_alert(alert)
            
        except Exception as e:
            self.logger.error(f"帧处理流水线错误: {e}")
            self.error_count += 1
            self.consecutive_errors += 1
        
        return alerts
    
    def _processing_loop(self) -> None:
        """主处理循环"""
        self.logger.info("开始处理循环")
        
        # 启动性能监控
        performance_monitor.start_monitoring()
        
        while self.is_running:
            frame_start_time = time.time()
            
            try:
                # 获取视频帧
                frame = self.video_capture.get_frame()
                if frame is None:
                    if not self._handle_video_error():
                        break
                    continue
                
                # 检查视频质量
                quality = self.video_processor.check_quality(frame)
                if quality < 0.5:  # Use hardcoded threshold for now
                    self.logger.warning(f"视频质量较低: {quality:.2f}")
                
                # 处理帧并记录性能
                detection_start = time.time()
                alerts = self.process_frame_pipeline(frame)
                detection_time = (time.time() - detection_start) * 1000  # 转换为毫秒
                
                # 更新统计信息
                self.frame_count += 1
                self.consecutive_errors = 0  # 重置连续错误计数
                self._update_fps()
                
                # 更新性能指标
                frame_time = (time.time() - frame_start_time) * 1000
                self._update_performance_metrics(
                    detection_time=detection_time,
                    pose_time=0.0,  # 这些时间在process_frame_pipeline中会更新
                    risk_time=0.0
                )
                
                # 控制处理频率
                time.sleep(1.0 / self.config.detection_fps)
                
            except Exception as e:
                self.logger.error(f"处理循环错误: {e}")
                self.logger.error(traceback.format_exc())
                self.error_count += 1
                self.consecutive_errors += 1
                
                # 使用异常处理器处理异常
                exception_handler.handle_exception(e, 'detection_system')
                
                # 检查是否需要恢复
                if not self._handle_processing_error():
                    break
        
        # 停止性能监控
        performance_monitor.stop_monitoring()
        self.logger.info("处理循环结束")
    
    def _handle_video_error(self) -> bool:
        """
        处理视频错误
        
        Returns:
            是否成功恢复
        """
        self.logger.warning("视频流中断，尝试重新连接...")
        
        if self.video_capture.reconnect():
            self.logger.info("视频流重新连接成功")
            return True
        
        self.consecutive_errors += 1
        if self.consecutive_errors >= self.max_consecutive_errors:
            self.logger.error("视频流连续错误次数过多，停止系统")
            return False
        
        # 等待后重试
        time.sleep(2.0)
        return True
    
    def _handle_processing_error(self) -> bool:
        """
        处理处理错误
        
        Returns:
            是否继续运行
        """
        if self.consecutive_errors >= self.max_consecutive_errors:
            self.recovery_attempts += 1
            
            if self.recovery_attempts >= self.max_recovery_attempts:
                self.logger.error("系统恢复尝试次数过多，停止运行")
                return False
            
            self.logger.warning(f"尝试系统恢复 ({self.recovery_attempts}/{self.max_recovery_attempts})")
            
            # 尝试重新初始化
            if self.initialize():
                self.consecutive_errors = 0
                self.logger.info("系统恢复成功")
            else:
                self.logger.error("系统恢复失败")
                return False
        
        # 短暂等待后继续
        time.sleep(1.0)
        return True
    
    def _update_fps(self) -> None:
        """更新FPS统计"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.last_fps_time)
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    def _clear_queues(self) -> None:
        """清空所有队列"""
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Empty:
                break
        
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except Empty:
                break
    def _setup_exception_handling(self) -> None:
        """设置异常处理"""
        try:
            # 注册检测系统模块
            exception_handler.register_module(
                'detection_system', 
                self._recovery_handler
            )
            
            # 设置恢复策略
            from ..core.exception_handler import RecoveryStrategy
            exception_handler.set_recovery_strategy(
                'ConnectionError', 
                RecoveryStrategy.RESTART_MODULE
            )
            exception_handler.set_recovery_strategy(
                'TimeoutError', 
                RecoveryStrategy.RETRY
            )
            exception_handler.set_recovery_strategy(
                'MemoryError', 
                RecoveryStrategy.RESTART_SYSTEM
            )
            
            self.logger.info("异常处理设置完成")
            
        except Exception as e:
            self.logger.error(f"异常处理设置失败: {e}")
    
    def _setup_performance_monitoring(self) -> None:
        """设置性能监控"""
        try:
            # 设置性能阈值
            performance_monitor.set_threshold('cpu_warning', 70.0)
            performance_monitor.set_threshold('cpu_critical', 80.0)
            performance_monitor.set_threshold('memory_warning', 60.0)
            performance_monitor.set_threshold('memory_critical', 70.0)
            performance_monitor.set_threshold('fps_warning', 10.0)
            performance_monitor.set_threshold('fps_critical', 5.0)
            
            # 注册优化回调
            performance_monitor.register_optimization_callback(
                'cpu_critical', 
                self._optimize_cpu_usage
            )
            performance_monitor.register_optimization_callback(
                'memory_critical', 
                self._optimize_memory_usage
            )
            performance_monitor.register_optimization_callback(
                'fps_critical', 
                self._optimize_processing_speed
            )
            
            self.logger.info("性能监控设置完成")
            
            # 注册系统恢复管理器
            system_recovery_manager.register_module(
                'detection_system', 
                lambda: self.is_running and not self._has_critical_errors()
            )
            
        except Exception as e:
            self.logger.error(f"性能监控设置失败: {e}")
    
    def _recovery_handler(self) -> bool:
        """恢复处理器"""
        try:
            self.logger.info("开始系统恢复...")
            
            # 停止当前运行
            if self.is_running:
                self.stop_detection()
            
            # 清理资源
            self._clear_queues()
            
            # 重新初始化
            if self.initialize():
                self.logger.info("系统恢复成功")
                return True
            else:
                self.logger.error("系统恢复失败")
                return False
                
        except Exception as e:
            self.logger.error(f"恢复处理器异常: {e}")
            return False
    
    def _optimize_cpu_usage(self, alert) -> None:
        """优化CPU使用率"""
        try:
            self.logger.info("开始CPU使用率优化...")
            
            # 降低处理频率
            if hasattr(self, 'frame_queue'):
                # 清理部分队列以减少处理负载
                queue_size = self.frame_queue.qsize()
                if queue_size > 5:
                    for _ in range(queue_size // 2):
                        try:
                            self.frame_queue.get_nowait()
                        except Empty:
                            break
            
            # 降低检测精度以提高速度
            if self.object_detector and hasattr(self.object_detector, 'set_optimization_mode'):
                self.object_detector.set_optimization_mode(True)
            
            self.logger.info("CPU使用率优化完成")
            
        except Exception as e:
            self.logger.error(f"CPU优化失败: {e}")
    
    def _optimize_memory_usage(self, alert) -> None:
        """优化内存使用率"""
        try:
            self.logger.info("开始内存使用率优化...")
            
            # 清理队列
            self._clear_queues()
            
            # 触发垃圾回收
            import gc
            gc.collect()
            
            # 减少缓存大小
            if hasattr(self, 'frame_queue'):
                # 重新创建更小的队列
                old_queue = self.frame_queue
                self.frame_queue = Queue(maxsize=5)
                del old_queue
            
            self.logger.info("内存使用率优化完成")
            
        except Exception as e:
            self.logger.error(f"内存优化失败: {e}")
    
    def _optimize_processing_speed(self, alert) -> None:
        """优化处理速度"""
        try:
            self.logger.info("开始处理速度优化...")
            
            # 跳过部分帧以提高FPS
            if hasattr(self, 'frame_skip_count'):
                self.frame_skip_count = 2  # 每3帧处理1帧
            else:
                self.frame_skip_count = 2
            
            # 降低检测精度
            if self.object_detector and hasattr(self.object_detector, 'confidence_threshold'):
                # 提高置信度阈值以减少检测数量
                current_threshold = getattr(self.object_detector, 'confidence_threshold', 0.5)
                new_threshold = min(0.8, current_threshold + 0.1)
                if hasattr(self.object_detector, 'set_confidence_threshold'):
                    self.object_detector.set_confidence_threshold(new_threshold)
            
            self.logger.info("处理速度优化完成")
            
        except Exception as e:
            self.logger.error(f"处理速度优化失败: {e}")
    
    def _update_performance_metrics(self, detection_time: float = 0.0,
                                  pose_time: float = 0.0,
                                  risk_time: float = 0.0) -> None:
        """更新性能指标"""
        try:
            # 更新处理时间
            self.processing_times = {
                'detection': detection_time,
                'pose_analysis': pose_time,
                'risk_assessment': risk_time,
                'total': detection_time + pose_time + risk_time
            }
            
            # 更新性能监控器
            queue_sizes = {
                'frame_queue': self.frame_queue.qsize(),
                'result_queue': self.result_queue.qsize()
            }
            
            performance_monitor.update_processing_metrics(
                fps=self.current_fps,
                frame_processing_time=self.processing_times['total'],
                detection_time=detection_time,
                pose_analysis_time=pose_time,
                queue_sizes=queue_sizes
            )
            
        except Exception as e:
            self.logger.error(f"性能指标更新失败: {e}")
    
    def get_enhanced_system_status(self) -> Dict[str, Any]:
        """获取增强的系统状态信息"""
        try:
            # 基础状态
            status = self.get_system_status()
            
            # 添加异常处理状态
            status['exception_handling'] = {
                'module_health': exception_handler.get_module_health('detection_system'),
                'exception_stats': exception_handler.get_exception_statistics(),
                'recent_exceptions': exception_handler.get_recent_exceptions(hours=1)
            }
            
            # 添加性能监控状态
            current_metrics = performance_monitor.get_current_metrics()
            status['performance_monitoring'] = {
                'current_metrics': current_metrics.__dict__ if current_metrics else None,
                'performance_summary': performance_monitor.get_performance_summary(minutes=30),
                'active_alerts': performance_monitor.get_active_alerts(),
                'performance_stats': performance_monitor.get_performance_statistics()
            }
            
            # 添加处理时间统计
            if hasattr(self, 'processing_times'):
                status['processing_times'] = self.processing_times.copy()
            
            return status
            
        except Exception as e:
            self.logger.error(f"获取增强状态失败: {e}")
            return self.get_system_status()
    
    def _has_critical_errors(self) -> bool:
        """
        检查是否有严重错误
        
        Returns:
            是否有严重错误
        """
        try:
            # 检查异常处理器中的模块健康状态
            health = exception_handler.get_module_health('detection_system')
            if health and not health.get('is_healthy', True):
                return True
            
            # 检查性能监控中的严重警报
            active_alerts = performance_monitor.get_active_alerts()
            for alert in active_alerts:
                if alert.get('level') == 'critical':
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查严重错误失败: {e}")
            return True  # 如果检查失败，假设有严重错误