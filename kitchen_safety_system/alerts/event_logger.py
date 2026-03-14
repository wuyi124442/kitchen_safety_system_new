"""
事件日志记录系统

实现详细的事件日志记录和视频片段自动保存功能。
满足需求 5.3 和 5.5。
"""

import time
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import threading

from ..core.interfaces import AlertEvent, AlertType, AlertLevel, ILogSystem
from ..core.models import LogRecord
from ..utils.logger import get_logger
from ..database.models import alert_repo, log_repo


@dataclass
class EventLogEntry:
    """事件日志条目"""
    event_id: str
    event_type: str
    alert_type: AlertType
    alert_level: AlertLevel
    timestamp: datetime
    location: Optional[tuple]
    description: str
    video_clip_path: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    detection_data: Optional[Dict[str, Any]] = None
    system_state: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'alert_type': self.alert_type.value,
            'alert_level': self.alert_level.value,
            'timestamp': self.timestamp.isoformat(),
            'location': self.location,
            'description': self.description,
            'video_clip_path': self.video_clip_path,
            'additional_data': self.additional_data,
            'detection_data': self.detection_data,
            'system_state': self.system_state
        }


class EventLogger(ILogSystem):
    """
    事件日志记录器
    
    功能特性：
    1. 详细事件信息记录
    2. 视频片段自动保存
    3. 结构化日志存储
    4. 事件查询和导出
    5. 实时事件监控
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化事件日志记录器
        
        Args:
            config: 配置参数
        """
        self.logger = get_logger(__name__)
        self.config = config or {}
        
        # 日志存储
        self.event_logs: Dict[str, EventLogEntry] = {}
        self.recent_events: List[EventLogEntry] = []
        
        # 视频缓存配置
        self.video_buffer_size = self.config.get('video_buffer_size', 30)  # 保存前后30帧
        self.video_frame_buffer: List = []
        self.max_buffer_size = self.config.get('max_buffer_size', 150)  # 最大缓存150帧
        
        # 存储配置
        self.log_dir = Path(self.config.get('log_dir', 'logs'))
        self.video_dir = Path(self.config.get('video_dir', 'logs/video_clips'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        
        # 线程安全
        self.lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'total_events': 0,
            'events_with_video': 0,
            'video_save_failures': 0,
            'database_save_failures': 0
        }
        
        self.logger.info("事件日志记录器已初始化")
    
    def log_alert_event(self, alert_event: AlertEvent, 
                       detection_data: Optional[Dict[str, Any]] = None,
                       system_state: Optional[Dict[str, Any]] = None,
                       video_frames: Optional[List] = None) -> str:
        """
        记录报警事件详细信息
        
        Args:
            alert_event: 报警事件
            detection_data: 检测数据（目标检测结果、姿态数据等）
            system_state: 系统状态信息
            video_frames: 相关视频帧
            
        Returns:
            str: 事件ID
        """
        with self.lock:
            try:
                # 生成事件ID
                event_id = str(uuid.uuid4())
                
                # 创建事件日志条目
                event_entry = EventLogEntry(
                    event_id=event_id,
                    event_type='alert',
                    alert_type=alert_event.alert_type,
                    alert_level=alert_event.alert_level,
                    timestamp=datetime.fromtimestamp(alert_event.timestamp),
                    location=alert_event.location,
                    description=alert_event.description,
                    additional_data=alert_event.additional_data,
                    detection_data=detection_data,
                    system_state=system_state
                )
                
                # 保存视频片段
                if video_frames:
                    video_path = self._save_video_clip(video_frames, event_id)
                    if video_path:
                        event_entry.video_clip_path = video_path
                        self.stats['events_with_video'] += 1
                    else:
                        self.stats['video_save_failures'] += 1
                
                # 存储事件
                self.event_logs[event_id] = event_entry
                self.recent_events.append(event_entry)
                
                # 限制内存中的事件数量
                if len(self.recent_events) > 1000:
                    self.recent_events = self.recent_events[-500:]
                
                # 保存到数据库
                self._save_to_database(event_entry)
                
                # 更新统计
                self.stats['total_events'] += 1
                
                self.logger.info(f"事件已记录: {event_id}, 类型: {alert_event.alert_type.value}")
                return event_id
                
            except Exception as e:
                self.logger.error(f"记录事件失败: {e}")
                return ""
    
    def update_video_buffer(self, frame) -> None:
        """
        更新视频帧缓存
        
        Args:
            frame: 视频帧
        """
        with self.lock:
            try:
                if frame is not None:
                    self.video_frame_buffer.append(frame.copy())
                    
                    # 限制缓存大小
                    if len(self.video_frame_buffer) > self.max_buffer_size:
                        self.video_frame_buffer.pop(0)
                        
            except Exception as e:
                self.logger.error(f"更新视频缓存失败: {e}")
    
    def get_buffered_frames(self, event_timestamp: float) -> List:
        """
        获取事件相关的缓存帧
        
        Args:
            event_timestamp: 事件时间戳
            
        Returns:
            List: 相关视频帧列表
        """
        with self.lock:
            try:
                # 简化实现：返回最近的缓存帧
                buffer_size = min(self.video_buffer_size, len(self.video_frame_buffer))
                if buffer_size > 0:
                    return self.video_frame_buffer[-buffer_size:].copy()
                return []
                
            except Exception as e:
                self.logger.error(f"获取缓存帧失败: {e}")
                return []
    
    def _save_video_clip(self, frames: List, event_id: str) -> Optional[str]:
        """
        保存视频片段
        
        Args:
            frames: 视频帧列表
            event_id: 事件ID
            
        Returns:
            Optional[str]: 保存的文件路径
        """
        try:
            import cv2
            
            if not frames:
                self.logger.warning(f"没有视频帧可保存，事件ID: {event_id}")
                return None
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"event_{event_id}_{timestamp}.mp4"
            filepath = self.video_dir / filename
            
            # 获取视频帧尺寸
            height, width = frames[0].shape[:2]
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = self.config.get('video_fps', 15)
            video_writer = cv2.VideoWriter(str(filepath), fourcc, fps, (width, height))
            
            if not video_writer.isOpened():
                self.logger.error(f"无法创建视频文件: {filepath}")
                return None
            
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
                if filepath.exists():
                    filepath.unlink()
                return None
                
        except ImportError:
            self.logger.error("OpenCV未安装，无法保存视频片段")
            return None
        except Exception as e:
            self.logger.error(f"保存视频片段失败: {e}")
            return None
    
    def _save_to_database(self, event_entry: EventLogEntry) -> bool:
        """
        保存事件到数据库
        
        Args:
            event_entry: 事件条目
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 创建日志记录
            log_record = LogRecord(
                level="INFO",
                message=f"Alert Event: {event_entry.description}",
                timestamp=event_entry.timestamp,
                module="event_logger",
                function="log_alert_event",
                additional_data=event_entry.to_dict()
            )
            
            # 保存到数据库
            result = log_repo.create(log_record)
            if result:
                self.logger.debug(f"事件已保存到数据库: {event_entry.event_id}")
                return True
            else:
                self.stats['database_save_failures'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"保存事件到数据库失败: {e}")
            self.stats['database_save_failures'] += 1
            return False
    
    def log_event(self, level: str, message: str, additional_data: Optional[Dict] = None) -> None:
        """
        记录一般日志事件
        
        Args:
            level: 日志级别
            message: 日志消息
            additional_data: 附加数据
        """
        try:
            log_record = LogRecord(
                level=level,
                message=message,
                timestamp=datetime.now(),
                module="event_logger",
                additional_data=additional_data
            )
            
            log_repo.create(log_record)
            self.logger.debug(f"日志事件已记录: {level} - {message}")
            
        except Exception as e:
            self.logger.error(f"记录日志事件失败: {e}")
    
    def query_logs(self, start_time: float, end_time: float, 
                   event_type: Optional[str] = None, 
                   level: Optional[str] = None) -> List[Dict]:
        """
        查询日志
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            event_type: 事件类型
            level: 日志级别
            
        Returns:
            List[Dict]: 日志记录列表
        """
        try:
            start_date = datetime.fromtimestamp(start_time)
            end_date = datetime.fromtimestamp(end_time)
            
            # 从数据库查询
            logs = log_repo.get_by_date_range(start_date, end_date)
            
            # 过滤条件
            filtered_logs = []
            for log in logs:
                if level and log.level != level:
                    continue
                
                if event_type and log.additional_data:
                    log_event_type = log.additional_data.get('event_type')
                    if log_event_type != event_type:
                        continue
                
                filtered_logs.append(log.to_dict())
            
            return filtered_logs
            
        except Exception as e:
            self.logger.error(f"查询日志失败: {e}")
            return []
    
    def export_logs(self, start_time: float, end_time: float, 
                    format_type: str = "json") -> str:
        """
        导出日志
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            format_type: 导出格式
            
        Returns:
            str: 导出文件路径
        """
        try:
            logs = self.query_logs(start_time, end_time)
            
            # 生成导出文件名
            start_date = datetime.fromtimestamp(start_time).strftime('%Y%m%d')
            end_date = datetime.fromtimestamp(end_time).strftime('%Y%m%d')
            filename = f"event_logs_{start_date}_to_{end_date}.{format_type}"
            filepath = self.log_dir / filename
            
            if format_type == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            self.logger.info(f"日志已导出: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"导出日志失败: {e}")
            return ""
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """
        获取事件统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self.lock:
            return {
                **self.stats,
                'recent_events_count': len(self.recent_events),
                'total_stored_events': len(self.event_logs),
                'video_buffer_size': len(self.video_frame_buffer)
            }
    
    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的事件
        
        Args:
            count: 返回数量
            
        Returns:
            List[Dict[str, Any]]: 事件列表
        """
        with self.lock:
            recent = self.recent_events[-count:] if count > 0 else self.recent_events
            return [event.to_dict() for event in reversed(recent)]
    
    def clear_old_events(self, days: int = 30) -> int:
        """
        清理旧事件
        
        Args:
            days: 保留天数
            
        Returns:
            int: 清理的事件数量
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # 清理内存中的事件
            old_count = len(self.recent_events)
            self.recent_events = [
                event for event in self.recent_events 
                if event.timestamp > cutoff_time
            ]
            
            # 清理事件日志
            old_events = [
                event_id for event_id, event in self.event_logs.items()
                if event.timestamp <= cutoff_time
            ]
            
            for event_id in old_events:
                del self.event_logs[event_id]
            
            cleaned_count = old_count - len(self.recent_events) + len(old_events)
            
            self.logger.info(f"已清理 {cleaned_count} 个旧事件")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理旧事件失败: {e}")
            return 0


# 全局事件日志记录器实例
event_logger = EventLogger()