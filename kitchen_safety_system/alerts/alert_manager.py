"""
报警管理器实现

实现多种报警方式支持、报警去重和频率控制功能。
"""

import time
import json
import hashlib
import threading
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path

from ..core.interfaces import (
    IAlertManager, AlertEvent, AlertType, AlertLevel
)
from ..core.models import SystemConfig
from ..utils.logger import get_logger
from .notification_channels import (
    NotificationChannel, NotificationConfig,
    SoundNotificationChannel, EmailNotificationChannel,
    SMSNotificationChannel, ConsoleNotificationChannel
)
from .event_logger import EventLogger


@dataclass
class AlertRecord:
    """报警记录数据结构"""
    alert_id: str
    alert_event: AlertEvent
    sent_channels: List[str] = field(default_factory=list)
    retry_count: int = 0
    created_time: float = field(default_factory=time.time)
    last_attempt_time: float = field(default_factory=time.time)
    is_resolved: bool = False


@dataclass
class DeduplicationRule:
    """去重规则配置"""
    alert_type: AlertType
    time_window: float  # 时间窗口（秒）
    location_threshold: Optional[float] = None  # 位置阈值（像素）
    description_similarity: float = 0.8  # 描述相似度阈值


@dataclass
class FrequencyLimit:
    """频率限制配置"""
    alert_type: AlertType
    max_count: int  # 最大次数
    time_window: float  # 时间窗口（秒）
    cooldown_time: float = 0.0  # 冷却时间（秒）


class AlertManager(IAlertManager):
    """
    报警管理器
    
    功能特性：
    1. 多种通知渠道支持（声音、邮件、短信、控制台）
    2. 报警去重机制
    3. 频率控制和冷却时间
    4. 报警优先级路由
    5. 报警历史记录和统计
    6. 配置管理和动态更新
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """
        初始化报警管理器
        
        Args:
            config: 系统配置对象
        """
        self.logger = get_logger(__name__)
        self.config = config or SystemConfig()
        
        # 注册异常处理
        from ..core.exception_handler import exception_handler
        exception_handler.register_module('alert_manager', self._recovery_handler)
        
        # 通知渠道
        self.notification_channels: Dict[str, NotificationChannel] = {}
        
        # 事件日志记录器
        self.event_logger = EventLogger()
        
        # 报警记录和历史
        self.alert_records: Dict[str, AlertRecord] = {}
        self.alert_history: deque = deque(maxlen=1000)  # 最多保存1000条历史记录
        
        # 去重和频率控制
        self.deduplication_rules: List[DeduplicationRule] = []
        self.frequency_limits: Dict[AlertType, FrequencyLimit] = {}
        self.alert_counts: Dict[str, deque] = defaultdict(lambda: deque())
        self.last_alert_times: Dict[str, float] = {}
        
        # 线程安全锁
        self.lock = threading.RLock()
        
        # 统计信息
        self.statistics = {
            'total_alerts': 0,
            'sent_alerts': 0,
            'deduplicated_alerts': 0,
            'rate_limited_alerts': 0,
            'failed_alerts': 0,
            'channel_stats': defaultdict(lambda: {'sent': 0, 'failed': 0})
        }
        
        # 初始化
        self._initialize_default_rules()
        self._initialize_notification_channels()
        
        self.logger.info("报警管理器已初始化")
    
    def _initialize_default_rules(self) -> None:
        """初始化默认的去重和频率限制规则"""
        # 默认去重规则
        self.deduplication_rules = [
            DeduplicationRule(
                alert_type=AlertType.FALL_DETECTED,
                time_window=30.0,  # 30秒内相同跌倒报警去重
                location_threshold=100.0  # 100像素内视为同一位置
            ),
            DeduplicationRule(
                alert_type=AlertType.UNATTENDED_STOVE,
                time_window=60.0,  # 60秒内相同无人看管报警去重
                location_threshold=50.0   # 50像素内视为同一灶台
            ),
            DeduplicationRule(
                alert_type=AlertType.SYSTEM_ERROR,
                time_window=120.0,  # 120秒内相同系统错误去重
                description_similarity=0.9  # 高相似度描述去重
            )
        ]
        
        # 默认频率限制
        self.frequency_limits = {
            AlertType.FALL_DETECTED: FrequencyLimit(
                alert_type=AlertType.FALL_DETECTED,
                max_count=3,
                time_window=300.0,  # 5分钟内最多3次
                cooldown_time=60.0   # 冷却60秒
            ),
            AlertType.UNATTENDED_STOVE: FrequencyLimit(
                alert_type=AlertType.UNATTENDED_STOVE,
                max_count=5,
                time_window=600.0,  # 10分钟内最多5次
                cooldown_time=30.0   # 冷却30秒
            ),
            AlertType.SYSTEM_ERROR: FrequencyLimit(
                alert_type=AlertType.SYSTEM_ERROR,
                max_count=10,
                time_window=3600.0,  # 1小时内最多10次
                cooldown_time=120.0   # 冷却120秒
            )
        }
    
    def _initialize_notification_channels(self) -> None:
        """初始化通知渠道"""
        try:
            # 控制台通知（默认启用）
            console_config = NotificationConfig(
                enabled=True,
                priority_levels=[AlertLevel.LOW, AlertLevel.MEDIUM, AlertLevel.HIGH, AlertLevel.CRITICAL],
                additional_settings={
                    'use_colors': True,
                    'show_timestamp': True
                }
            )
            self.notification_channels['console'] = ConsoleNotificationChannel(console_config)
            
            # 声音通知
            sound_config = NotificationConfig(
                enabled=self.config.enable_sound_alert,
                priority_levels=[AlertLevel.MEDIUM, AlertLevel.HIGH, AlertLevel.CRITICAL],
                additional_settings={
                    'sound_files': {
                        'fall_detected': 'sounds/fall_alert.wav',
                        'unattended_stove': 'sounds/stove_alert.wav',
                        'system_error': 'sounds/error_alert.wav'
                    },
                    'volume': 0.8
                }
            )
            self.notification_channels['sound'] = SoundNotificationChannel(sound_config)
            
            # 邮件通知
            email_config = NotificationConfig(
                enabled=self.config.enable_email_alert,
                priority_levels=[AlertLevel.HIGH, AlertLevel.CRITICAL],
                additional_settings={
                    'smtp_server': getattr(self.config, 'email_smtp_server', 'smtp.gmail.com'),
                    'smtp_port': getattr(self.config, 'email_smtp_port', 587),
                    'username': getattr(self.config, 'email_username', ''),
                    'password': getattr(self.config, 'email_password', ''),
                    'to_emails': getattr(self.config, 'email_recipients', []),
                    'use_tls': True
                }
            )
            self.notification_channels['email'] = EmailNotificationChannel(email_config)
            
            # 短信通知
            sms_config = NotificationConfig(
                enabled=self.config.enable_sms_alert,
                priority_levels=[AlertLevel.CRITICAL],
                additional_settings={
                    'api_url': getattr(self.config, 'sms_api_url', ''),
                    'api_key': getattr(self.config, 'sms_api_key', ''),
                    'api_secret': getattr(self.config, 'sms_api_secret', ''),
                    'phone_numbers': getattr(self.config, 'sms_recipients', []),
                    'sender_id': 'KitchenSafety'
                }
            )
            self.notification_channels['sms'] = SMSNotificationChannel(sms_config)
            
            # 初始化所有渠道
            for name, channel in self.notification_channels.items():
                if channel.config.enabled:
                    if channel.initialize():
                        self.logger.info(f"通知渠道 '{name}' 初始化成功")
                    else:
                        self.logger.warning(f"通知渠道 '{name}' 初始化失败")
                        
        except Exception as e:
            self.logger.error(f"初始化通知渠道失败: {e}")
    
    def trigger_alert(self, alert_event: AlertEvent, 
                       detection_data: Optional[Dict[str, Any]] = None,
                       system_state: Optional[Dict[str, Any]] = None) -> bool:
            """
            触发报警

            Args:
                alert_event: 报警事件
                detection_data: 检测数据（目标检测结果、姿态数据等）
                system_state: 系统状态信息

            Returns:
                bool: 是否成功处理报警
            """
            with self.lock:
                try:
                    self.statistics['total_alerts'] += 1

                    # 生成报警ID
                    alert_id = self._generate_alert_id(alert_event)

                    # 检查去重
                    if self._is_duplicate_alert(alert_event):
                        self.statistics['deduplicated_alerts'] += 1
                        self.logger.debug(f"报警已去重: {alert_id}")
                        return True

                    # 检查频率限制
                    if self._is_rate_limited(alert_event):
                        self.statistics['rate_limited_alerts'] += 1
                        self.logger.debug(f"报警被频率限制: {alert_id}")
                        return True

                    # 获取相关视频帧
                    video_frames = self.event_logger.get_buffered_frames(alert_event.timestamp)

                    # 记录详细事件信息（需求 5.3 和 5.5）
                    event_id = self.event_logger.log_alert_event(
                        alert_event=alert_event,
                        detection_data=detection_data,
                        system_state=system_state,
                        video_frames=video_frames
                    )

                    # 创建报警记录
                    alert_record = AlertRecord(
                        alert_id=alert_id,
                        alert_event=alert_event
                    )

                    # 发送通知
                    success = self._send_notifications(alert_record)

                    # 记录报警
                    self.alert_records[alert_id] = alert_record
                    self.alert_history.append(alert_record)

                    # 更新统计
                    if success:
                        self.statistics['sent_alerts'] += 1
                    else:
                        self.statistics['failed_alerts'] += 1

                    # 更新频率计数
                    self._update_frequency_counters(alert_event)

                    self.logger.info(f"报警处理完成: {alert_id}, 事件ID: {event_id}, 成功: {success}")
                    return success

                except Exception as e:
                    self.logger.error(f"触发报警失败: {e}")
                    # 使用异常处理器记录异常
                    from ..core.exception_handler import exception_handler
                    exception_handler.handle_exception(e, 'alert_manager')
                    self.statistics['failed_alerts'] += 1
                    return False

    
    def send_notification(self, alert_event: AlertEvent, method: str) -> bool:
        """
        发送指定方式的通知
        
        Args:
            alert_event: 报警事件
            method: 通知方式
            
        Returns:
            bool: 是否发送成功
        """
        try:
            channel = self.notification_channels.get(method)
            if not channel:
                self.logger.error(f"未找到通知渠道: {method}")
                return False
            
            success = channel.send_with_retry(alert_event)
            
            # 更新统计
            if success:
                self.statistics['channel_stats'][method]['sent'] += 1
            else:
                self.statistics['channel_stats'][method]['failed'] += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"发送通知失败 ({method}): {e}")
            self.statistics['channel_stats'][method]['failed'] += 1
            return False
    
    def record_event(self, alert_event: AlertEvent, 
                      detection_data: Optional[Dict[str, Any]] = None,
                      system_state: Optional[Dict[str, Any]] = None) -> bool:
            """
            记录事件（不发送通知）

            Args:
                alert_event: 报警事件
                detection_data: 检测数据
                system_state: 系统状态信息

            Returns:
                bool: 是否记录成功
            """
            try:
                alert_id = self._generate_alert_id(alert_event)

                # 获取相关视频帧
                video_frames = self.event_logger.get_buffered_frames(alert_event.timestamp)

                # 记录详细事件信息（需求 5.3 和 5.5）
                event_id = self.event_logger.log_alert_event(
                    alert_event=alert_event,
                    detection_data=detection_data,
                    system_state=system_state,
                    video_frames=video_frames
                )

                alert_record = AlertRecord(
                    alert_id=alert_id,
                    alert_event=alert_event
                )

                self.alert_records[alert_id] = alert_record
                self.alert_history.append(alert_record)

                self.logger.debug(f"事件已记录: {alert_id}, 事件ID: {event_id}")
                return True

            except Exception as e:
                self.logger.error(f"记录事件失败: {e}")
                return False

    
    def save_video_clip(self, frames: List, event_id: str) -> str:
            """
            保存视频片段

            Args:
                frames: 视频帧列表
                event_id: 事件ID

            Returns:
                str: 保存的文件路径
            """
            try:
                import cv2

                # 创建保存目录
                save_dir = Path("logs/video_clips")
                save_dir.mkdir(parents=True, exist_ok=True)

                # 生成文件名
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f"alert_{event_id}_{timestamp}.mp4"
                filepath = save_dir / filename

                if not frames:
                    self.logger.warning(f"没有视频帧可保存，事件ID: {event_id}")
                    return ""

                # 获取视频帧尺寸
                height, width = frames[0].shape[:2]

                # 创建视频写入器
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                fps = 15  # 默认帧率
                video_writer = cv2.VideoWriter(str(filepath), fourcc, fps, (width, height))

                if not video_writer.isOpened():
                    self.logger.error(f"无法创建视频文件: {filepath}")
                    return ""

                # 写入视频帧
                frames_written = 0
                for frame in frames:
                    if frame is not None and frame.size > 0:
                        video_writer.write(frame)
                        frames_written += 1

                video_writer.release()

                if frames_written > 0:
                    self.logger.info(f"视频片段已保存: {filepath}, 帧数: {frames_written}")
                    return str(filepath)
                else:
                    self.logger.warning(f"没有有效帧写入视频文件: {filepath}")
                    # 删除空文件
                    if filepath.exists():
                        filepath.unlink()
                    return ""

            except ImportError:
                self.logger.error("OpenCV未安装，无法保存视频片段")
                return ""
            except Exception as e:
                self.logger.error(f"保存视频片段失败: {e}")
                return ""

    
    def _generate_alert_id(self, alert_event: AlertEvent) -> str:
        """生成报警ID"""
        content = f"{alert_event.alert_type.value}_{alert_event.timestamp}_{alert_event.description}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _is_duplicate_alert(self, alert_event: AlertEvent) -> bool:
        """检查是否为重复报警"""
        current_time = time.time()
        
        for rule in self.deduplication_rules:
            if rule.alert_type != alert_event.alert_type:
                continue
            
            # 检查时间窗口内的历史报警
            for record in reversed(self.alert_history):
                if current_time - record.created_time > rule.time_window:
                    break
                
                if record.alert_event.alert_type != alert_event.alert_type:
                    continue
                
                # 检查位置相似性
                if rule.location_threshold and alert_event.location and record.alert_event.location:
                    distance = self._calculate_distance(alert_event.location, record.alert_event.location)
                    if distance <= rule.location_threshold:
                        return True
                
                # 检查描述相似性
                if rule.description_similarity:
                    similarity = self._calculate_text_similarity(
                        alert_event.description, 
                        record.alert_event.description
                    )
                    if similarity >= rule.description_similarity:
                        return True
        
        return False
    
    def _is_rate_limited(self, alert_event: AlertEvent) -> bool:
        """检查是否被频率限制"""
        current_time = time.time()
        alert_type = alert_event.alert_type
        
        # 检查冷却时间
        last_time = self.last_alert_times.get(alert_type.value, 0)
        limit = self.frequency_limits.get(alert_type)
        
        if limit and current_time - last_time < limit.cooldown_time:
            return True
        
        # 检查频率限制
        if limit:
            count_key = alert_type.value
            counts = self.alert_counts[count_key]
            
            # 清理过期计数
            while counts and current_time - counts[0] > limit.time_window:
                counts.popleft()
            
            # 检查是否超过限制
            if len(counts) >= limit.max_count:
                return True
        
        return False
    
    def _send_notifications(self, alert_record: AlertRecord) -> bool:
        """发送通知到所有适当的渠道"""
        alert_event = alert_record.alert_event
        success_count = 0
        total_channels = 0
        
        for channel_name, channel in self.notification_channels.items():
            if not channel.config.enabled:
                continue
                
            if not channel.should_notify(alert_event):
                continue
                
            total_channels += 1
            
            if channel.send_with_retry(alert_event):
                alert_record.sent_channels.append(channel_name)
                success_count += 1
                self.statistics['channel_stats'][channel_name]['sent'] += 1
            else:
                self.statistics['channel_stats'][channel_name]['failed'] += 1
        
        # 如果至少有一个渠道成功，视为成功
        return success_count > 0 if total_channels > 0 else True
    
    def _update_frequency_counters(self, alert_event: AlertEvent) -> None:
        """更新频率计数器"""
        current_time = time.time()
        alert_type = alert_event.alert_type
        
        # 更新计数
        count_key = alert_type.value
        self.alert_counts[count_key].append(current_time)
        
        # 更新最后报警时间
        self.last_alert_times[alert_type.value] = current_time
    
    def _calculate_distance(self, point1: tuple, point2: tuple) -> float:
        """计算两点距离"""
        if not point1 or not point2:
            return float('inf')
        
        x1, y1 = point1
        x2, y2 = point2
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单实现）"""
        if not text1 or not text2:
            return 0.0
        
        # 简单的字符级相似度计算
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取报警统计信息"""
        with self.lock:
            stats = dict(self.statistics)
            
            # 添加实时统计
            stats['active_alerts'] = len([r for r in self.alert_records.values() if not r.is_resolved])
            stats['total_records'] = len(self.alert_records)
            stats['history_size'] = len(self.alert_history)
            
            # 渠道统计
            stats['channel_stats'] = dict(self.statistics['channel_stats'])
            
            return stats
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的报警记录"""
        with self.lock:
            recent = list(self.alert_history)[-count:]
            return [
                {
                    'alert_id': record.alert_id,
                    'alert_type': record.alert_event.alert_type.value,
                    'alert_level': record.alert_event.alert_level.value,
                    'description': record.alert_event.description,
                    'timestamp': record.alert_event.timestamp,
                    'location': record.alert_event.location,
                    'sent_channels': record.sent_channels,
                    'is_resolved': record.is_resolved
                }
                for record in reversed(recent)
            ]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """标记报警为已解决"""
        with self.lock:
            if alert_id in self.alert_records:
                self.alert_records[alert_id].is_resolved = True
                self.logger.info(f"报警已标记为解决: {alert_id}")
                return True
            return False
    
    def update_channel_config(self, channel_name: str, config: NotificationConfig) -> bool:
        """更新通知渠道配置"""
        try:
            if channel_name in self.notification_channels:
                old_channel = self.notification_channels[channel_name]
                
                # 创建新的渠道实例
                channel_class = type(old_channel)
                new_channel = channel_class(config)
                
                if new_channel.initialize():
                    self.notification_channels[channel_name] = new_channel
                    self.logger.info(f"通知渠道 '{channel_name}' 配置已更新")
                    return True
                else:
                    self.logger.error(f"通知渠道 '{channel_name}' 配置更新失败")
                    return False
            else:
                self.logger.error(f"未找到通知渠道: {channel_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新通知渠道配置失败: {e}")
            return False
    
    def add_deduplication_rule(self, rule: DeduplicationRule) -> None:
        """添加去重规则"""
        with self.lock:
            self.deduplication_rules.append(rule)
            self.logger.info(f"已添加去重规则: {rule.alert_type.value}")
    
    def add_frequency_limit(self, limit: FrequencyLimit) -> None:
        """添加频率限制"""
        with self.lock:
            self.frequency_limits[limit.alert_type] = limit
            self.logger.info(f"已添加频率限制: {limit.alert_type.value}")
    
    def clear_alert_history(self) -> None:
        """清空报警历史"""
        with self.lock:
            self.alert_history.clear()
            self.alert_records.clear()
            self.alert_counts.clear()
            self.last_alert_times.clear()
            
            # 重置统计
            self.statistics = {
                'total_alerts': 0,
                'sent_alerts': 0,
                'deduplicated_alerts': 0,
                'rate_limited_alerts': 0,
                'failed_alerts': 0,
                'channel_stats': defaultdict(lambda: {'sent': 0, 'failed': 0})
            }
            
            self.logger.info("报警历史已清空")
    
    def update_video_buffer(self, frame) -> None:
        """
        更新视频帧缓存
        
        Args:
            frame: 视频帧
        """
        try:
            self.event_logger.update_video_buffer(frame)
        except Exception as e:
            self.logger.error(f"更新视频缓存失败: {e}")
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """
        获取事件统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            alert_stats = self.get_alert_statistics()
            event_stats = self.event_logger.get_event_statistics()
            
            return {
                'alert_stats': alert_stats,
                'event_stats': event_stats
            }
        except Exception as e:
            self.logger.error(f"获取事件统计失败: {e}")
            return {}
    
    def get_recent_events_detailed(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的详细事件
        
        Args:
            count: 返回数量
            
        Returns:
            List[Dict[str, Any]]: 事件列表
        """
        try:
            return self.event_logger.get_recent_events(count)
        except Exception as e:
            self.logger.error(f"获取最近事件失败: {e}")
            return []
    
    def export_event_logs(self, start_time: float, end_time: float, 
                         format_type: str = "json") -> str:
        """
        导出事件日志
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            format_type: 导出格式
            
        Returns:
            str: 导出文件路径
        """
        try:
            return self.event_logger.export_logs(start_time, end_time, format_type)
        except Exception as e:
            self.logger.error(f"导出事件日志失败: {e}")
            return ""
    
    def update_video_buffer(self, frame) -> None:
        """
        更新视频帧缓存

        Args:
            frame: 视频帧
        """
        try:
            self.event_logger.update_video_buffer(frame)
        except Exception as e:
            self.logger.error(f"更新视频缓存失败: {e}")

    def get_event_statistics(self) -> Dict[str, Any]:
        """
        获取事件统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            alert_stats = self.get_alert_statistics()
            event_stats = self.event_logger.get_event_statistics()

            return {
                'alert_stats': alert_stats,
                'event_stats': event_stats
            }
        except Exception as e:
            self.logger.error(f"获取事件统计失败: {e}")
            return {}

    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的事件

        Args:
            count: 返回数量

        Returns:
            List[Dict[str, Any]]: 事件列表
        """
        try:
            return self.event_logger.get_recent_events(count)
        except Exception as e:
            self.logger.error(f"获取最近事件失败: {e}")
            return []

    def export_event_logs(self, start_time: float, end_time: float,
                         format_type: str = "json") -> str:
        """
        导出事件日志

        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            format_type: 导出格式

        Returns:
            str: 导出文件路径
        """
        try:
            return self.event_logger.export_logs(start_time, end_time, format_type)
        except Exception as e:
            self.logger.error(f"导出事件日志失败: {e}")
            return ""
    
    def _recovery_handler(self) -> bool:
        """
        报警管理器恢复处理器
        
        Returns:
            是否恢复成功
        """
        try:
            self.logger.info("开始报警管理器恢复...")
            
            # 重置统计信息
            self.statistics = {
                'total_alerts': 0,
                'successful_alerts': 0,
                'duplicate_alerts': 0,
                'rate_limited_alerts': 0,
                'failed_alerts': 0,
                'channel_stats': defaultdict(lambda: {'sent': 0, 'failed': 0})
            }
            
            # 清理旧的报警记录（保留最近的100条）
            if len(self.alert_history) > 100:
                recent_records = list(self.alert_history)[-100:]
                self.alert_history.clear()
                self.alert_history.extend(recent_records)
            
            # 重新初始化通知渠道
            self._initialize_notification_channels()
            
            self.logger.info("报警管理器恢复成功")
            return True
            
        except Exception as e:
            self.logger.error(f"报警管理器恢复失败: {e}")
            return False