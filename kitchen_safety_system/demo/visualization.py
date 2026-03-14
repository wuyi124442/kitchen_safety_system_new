"""
检测结果可视化实现

提供实时检测框和标签显示，报警信息可视化展示。
需求: 10.2, 10.3, 10.4
"""

import cv2
import numpy as np
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..core.interfaces import DetectionResult, DetectionType, BoundingBox, AlertType, AlertLevel
from ..core.models import AlertRecord
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VisualizationTheme(Enum):
    """可视化主题"""
    DEFAULT = "default"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"


@dataclass
class ColorScheme:
    """颜色方案"""
    person: Tuple[int, int, int] = (0, 255, 0)      # 绿色
    stove: Tuple[int, int, int] = (255, 165, 0)     # 橙色
    flame: Tuple[int, int, int] = (0, 0, 255)       # 红色
    fall_alert: Tuple[int, int, int] = (0, 0, 255)  # 红色
    stove_alert: Tuple[int, int, int] = (255, 0, 255)  # 紫色
    background: Tuple[int, int, int] = (0, 0, 0)    # 黑色
    text: Tuple[int, int, int] = (255, 255, 255)    # 白色
    info_panel: Tuple[int, int, int] = (50, 50, 50) # 深灰色


class DetectionVisualizer:
    """
    检测结果可视化器
    
    提供实时检测框和标签显示功能。
    需求: 10.2, 10.4
    """
    
    def __init__(self, theme: VisualizationTheme = VisualizationTheme.DEFAULT):
        """
        初始化可视化器
        
        Args:
            theme: 可视化主题
        """
        self.theme = theme
        self.color_scheme = self._get_color_scheme(theme)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
        self.box_thickness = 2
        
        # 可视化选项
        self.show_confidence = True
        self.show_detection_id = False
        self.show_tracking_trail = False
        self.show_fps = True
        self.show_statistics = True
        
        # 性能统计
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        logger.info(f"检测结果可视化器初始化完成，主题: {theme.value}")
    
    def _get_color_scheme(self, theme: VisualizationTheme) -> ColorScheme:
        """获取颜色方案"""
        if theme == VisualizationTheme.DARK:
            return ColorScheme(
                person=(100, 255, 100),
                stove=(255, 200, 100),
                flame=(100, 100, 255),
                fall_alert=(255, 100, 100),
                stove_alert=(255, 100, 255),
                background=(30, 30, 30),
                text=(200, 200, 200),
                info_panel=(60, 60, 60)
            )
        elif theme == VisualizationTheme.HIGH_CONTRAST:
            return ColorScheme(
                person=(0, 255, 0),
                stove=(255, 255, 0),
                flame=(255, 0, 0),
                fall_alert=(255, 0, 0),
                stove_alert=(255, 0, 255),
                background=(0, 0, 0),
                text=(255, 255, 255),
                info_panel=(128, 128, 128)
            )
        else:  # DEFAULT
            return ColorScheme()
    
    def visualize_detections(self, 
                           frame: np.ndarray, 
                           detections: List[DetectionResult],
                           additional_info: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        在帧上可视化检测结果
        
        Args:
            frame: 输入图像帧
            detections: 检测结果列表
            additional_info: 附加信息
            
        Returns:
            可视化后的图像帧
        """
        if frame is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 复制帧以避免修改原始数据
        vis_frame = frame.copy()
        
        # 绘制检测框和标签
        for detection in detections:
            self._draw_detection(vis_frame, detection)
        
        # 绘制信息面板
        if self.show_statistics or self.show_fps:
            self._draw_info_panel(vis_frame, detections, additional_info)
        
        # 更新FPS统计
        self._update_fps()
        
        return vis_frame
    
    def _draw_detection(self, frame: np.ndarray, detection: DetectionResult) -> None:
        """绘制单个检测结果"""
        bbox = detection.bbox
        detection_type = detection.detection_type
        
        # 获取颜色
        color = self._get_detection_color(detection_type)
        
        # 绘制边界框
        cv2.rectangle(
            frame,
            (bbox.x, bbox.y),
            (bbox.x + bbox.width, bbox.y + bbox.height),
            color,
            self.box_thickness
        )
        
        # 准备标签文本
        label_parts = [detection_type.value]
        
        if self.show_confidence:
            label_parts.append(f"{bbox.confidence:.2f}")
        
        if self.show_detection_id and hasattr(detection, 'detection_id'):
            label_parts.append(f"ID:{detection.detection_id}")
        
        label = " | ".join(label_parts)
        
        # 计算标签背景尺寸
        (text_width, text_height), baseline = cv2.getTextSize(
            label, self.font, self.font_scale, self.font_thickness
        )
        
        # 绘制标签背景
        label_y = max(bbox.y - 10, text_height + 10)
        cv2.rectangle(
            frame,
            (bbox.x, label_y - text_height - 5),
            (bbox.x + text_width + 10, label_y + 5),
            color,
            -1
        )
        
        # 绘制标签文本
        cv2.putText(
            frame,
            label,
            (bbox.x + 5, label_y - 5),
            self.font,
            self.font_scale,
            self.color_scheme.text,
            self.font_thickness
        )
        
        # 绘制中心点
        center_x, center_y = bbox.center
        cv2.circle(frame, (int(center_x), int(center_y)), 3, color, -1)
    
    def _get_detection_color(self, detection_type: DetectionType) -> Tuple[int, int, int]:
        """获取检测类型对应的颜色"""
        color_map = {
            DetectionType.PERSON: self.color_scheme.person,
            DetectionType.STOVE: self.color_scheme.stove,
            DetectionType.FLAME: self.color_scheme.flame
        }
        return color_map.get(detection_type, (128, 128, 128))
    
    def _draw_info_panel(self, 
                        frame: np.ndarray, 
                        detections: List[DetectionResult],
                        additional_info: Optional[Dict[str, Any]] = None) -> None:
        """绘制信息面板"""
        height, width = frame.shape[:2]
        panel_width = 300
        panel_height = 150
        
        # 绘制面板背景
        cv2.rectangle(
            frame,
            (width - panel_width - 10, 10),
            (width - 10, panel_height + 10),
            self.color_scheme.info_panel,
            -1
        )
        
        # 绘制边框
        cv2.rectangle(
            frame,
            (width - panel_width - 10, 10),
            (width - 10, panel_height + 10),
            self.color_scheme.text,
            1
        )
        
        # 准备信息文本
        info_lines = []
        
        if self.show_fps:
            info_lines.append(f"FPS: {self.current_fps:.1f}")
        
        if self.show_statistics:
            # 统计检测结果
            detection_counts = {}
            for detection in detections:
                det_type = detection.detection_type.value
                detection_counts[det_type] = detection_counts.get(det_type, 0) + 1
            
            info_lines.append(f"Total: {len(detections)}")
            for det_type, count in detection_counts.items():
                info_lines.append(f"{det_type}: {count}")
        
        # 添加附加信息
        if additional_info:
            for key, value in additional_info.items():
                if isinstance(value, (int, float)):
                    info_lines.append(f"{key}: {value:.2f}")
                else:
                    info_lines.append(f"{key}: {value}")
        
        # 绘制信息文本
        y_offset = 30
        for line in info_lines:
            cv2.putText(
                frame,
                line,
                (width - panel_width, y_offset),
                self.font,
                0.5,
                self.color_scheme.text,
                1
            )
            y_offset += 20
    
    def _update_fps(self) -> None:
        """更新FPS统计"""
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def set_visualization_options(self, **options) -> None:
        """设置可视化选项"""
        for key, value in options.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"设置可视化选项: {key} = {value}")


class AlertVisualizer:
    """
    报警信息可视化器
    
    提供报警信息可视化展示功能。
    需求: 10.3, 10.4
    """
    
    def __init__(self, theme: VisualizationTheme = VisualizationTheme.DEFAULT):
        """
        初始化报警可视化器
        
        Args:
            theme: 可视化主题
        """
        self.theme = theme
        self.color_scheme = self._get_color_scheme(theme)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
        # 报警显示配置
        self.alert_display_duration = 5.0  # 报警显示持续时间（秒）
        self.max_alerts_display = 5        # 最大同时显示报警数量
        
        # 当前活跃报警
        self.active_alerts: List[Dict[str, Any]] = []
        
        # 动画效果
        self.blink_interval = 0.5  # 闪烁间隔
        self.last_blink_time = time.time()
        self.blink_state = True
        
        logger.info(f"报警可视化器初始化完成，主题: {theme.value}")
    
    def _get_color_scheme(self, theme: VisualizationTheme) -> ColorScheme:
        """获取颜色方案"""
        if theme == VisualizationTheme.DARK:
            return ColorScheme(
                fall_alert=(255, 100, 100),
                stove_alert=(255, 200, 100),
                background=(40, 40, 40),
                text=(220, 220, 220),
                info_panel=(70, 70, 70)
            )
        elif theme == VisualizationTheme.HIGH_CONTRAST:
            return ColorScheme(
                fall_alert=(255, 0, 0),
                stove_alert=(255, 255, 0),
                background=(0, 0, 0),
                text=(255, 255, 255),
                info_panel=(128, 128, 128)
            )
        else:  # DEFAULT
            return ColorScheme()
    
    def add_alert(self, alert_type: str, message: str, location: Optional[Tuple[int, int]] = None, **kwargs) -> None:
        """
        添加报警信息
        
        Args:
            alert_type: 报警类型
            message: 报警消息
            location: 报警位置 (x, y)
            **kwargs: 其他报警参数
        """
        alert = {
            'type': alert_type,
            'message': message,
            'location': location,
            'timestamp': time.time(),
            'level': kwargs.get('level', 'high'),
            'duration': kwargs.get('duration', self.alert_display_duration),
            **kwargs
        }
        
        self.active_alerts.append(alert)
        
        # 限制显示数量
        if len(self.active_alerts) > self.max_alerts_display:
            self.active_alerts = self.active_alerts[-self.max_alerts_display:]
        
        logger.info(f"添加报警: {alert_type} - {message}")
    
    def visualize_alerts(self, frame: np.ndarray) -> np.ndarray:
        """
        在帧上可视化报警信息
        
        Args:
            frame: 输入图像帧
            
        Returns:
            可视化后的图像帧
        """
        if frame is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 复制帧以避免修改原始数据
        vis_frame = frame.copy()
        
        # 更新闪烁状态
        self._update_blink_state()
        
        # 清理过期报警
        self._cleanup_expired_alerts()
        
        # 绘制报警信息
        self._draw_alert_panel(vis_frame)
        self._draw_alert_indicators(vis_frame)
        
        return vis_frame
    
    def _update_blink_state(self) -> None:
        """更新闪烁状态"""
        current_time = time.time()
        if current_time - self.last_blink_time >= self.blink_interval:
            self.blink_state = not self.blink_state
            self.last_blink_time = current_time
    
    def _cleanup_expired_alerts(self) -> None:
        """清理过期报警"""
        current_time = time.time()
        self.active_alerts = [
            alert for alert in self.active_alerts
            if current_time - alert['timestamp'] < alert['duration']
        ]
    
    def _draw_alert_panel(self, frame: np.ndarray) -> None:
        """绘制报警面板"""
        if not self.active_alerts:
            return
        
        height, width = frame.shape[:2]
        panel_width = 400
        panel_height = min(200, 40 + len(self.active_alerts) * 30)
        
        # 绘制面板背景
        panel_color = self.color_scheme.info_panel
        if any(alert['level'] == 'high' for alert in self.active_alerts) and self.blink_state:
            # 高级别报警时闪烁背景
            panel_color = (50, 50, 100)
        
        cv2.rectangle(
            frame,
            (10, height - panel_height - 10),
            (panel_width + 10, height - 10),
            panel_color,
            -1
        )
        
        # 绘制边框
        border_color = self.color_scheme.fall_alert if any(
            alert['level'] == 'high' for alert in self.active_alerts
        ) else self.color_scheme.text
        
        cv2.rectangle(
            frame,
            (10, height - panel_height - 10),
            (panel_width + 10, height - 10),
            border_color,
            2
        )
        
        # 绘制标题
        cv2.putText(
            frame,
            "ALERTS",
            (20, height - panel_height + 20),
            self.font,
            0.7,
            self.color_scheme.text,
            2
        )
        
        # 绘制报警列表
        y_offset = height - panel_height + 50
        for i, alert in enumerate(self.active_alerts[-5:]):  # 只显示最新的5个
            alert_color = self._get_alert_color(alert['type'], alert['level'])
            
            # 绘制报警图标
            cv2.circle(frame, (30, y_offset - 5), 5, alert_color, -1)
            
            # 绘制报警文本
            alert_text = f"{alert['type']}: {alert['message']}"
            if len(alert_text) > 45:
                alert_text = alert_text[:42] + "..."
            
            cv2.putText(
                frame,
                alert_text,
                (45, y_offset),
                self.font,
                0.5,
                self.color_scheme.text,
                1
            )
            
            y_offset += 25
    
    def _draw_alert_indicators(self, frame: np.ndarray) -> None:
        """绘制报警位置指示器"""
        for alert in self.active_alerts:
            if alert.get('location'):
                x, y = alert['location']
                alert_color = self._get_alert_color(alert['type'], alert['level'])
                
                # 绘制闪烁的圆圈指示器
                if self.blink_state:
                    cv2.circle(frame, (x, y), 20, alert_color, 3)
                    cv2.circle(frame, (x, y), 30, alert_color, 2)
                
                # 绘制报警类型标签
                label = alert['type'].upper()
                cv2.putText(
                    frame,
                    label,
                    (x - 30, y - 40),
                    self.font,
                    0.6,
                    alert_color,
                    2
                )
    
    def _get_alert_color(self, alert_type: str, alert_level: str) -> Tuple[int, int, int]:
        """获取报警颜色"""
        if alert_level == 'high':
            if 'fall' in alert_type.lower():
                return self.color_scheme.fall_alert
            else:
                return self.color_scheme.stove_alert
        else:
            return (255, 255, 0)  # 黄色表示中等级别
    
    def clear_alerts(self) -> None:
        """清除所有报警"""
        self.active_alerts.clear()
        logger.info("清除所有报警信息")
    
    def get_alert_count(self) -> int:
        """获取当前报警数量"""
        return len(self.active_alerts)


class ComprehensiveVisualizer:
    """
    综合可视化器
    
    整合检测结果和报警信息的可视化功能。
    """
    
    def __init__(self, theme: VisualizationTheme = VisualizationTheme.DEFAULT):
        """
        初始化综合可视化器
        
        Args:
            theme: 可视化主题
        """
        self.detection_visualizer = DetectionVisualizer(theme)
        self.alert_visualizer = AlertVisualizer(theme)
        self.theme = theme
        
        logger.info(f"综合可视化器初始化完成，主题: {theme.value}")
    
    def visualize_frame(self, 
                       frame: np.ndarray,
                       detections: List[DetectionResult],
                       alerts: Optional[List[Dict[str, Any]]] = None,
                       additional_info: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        综合可视化帧
        
        Args:
            frame: 输入图像帧
            detections: 检测结果列表
            alerts: 报警信息列表
            additional_info: 附加信息
            
        Returns:
            可视化后的图像帧
        """
        # 首先可视化检测结果
        vis_frame = self.detection_visualizer.visualize_detections(
            frame, detections, additional_info
        )
        
        # 添加新的报警信息
        if alerts:
            for alert in alerts:
                self.alert_visualizer.add_alert(**alert)
        
        # 可视化报警信息
        vis_frame = self.alert_visualizer.visualize_alerts(vis_frame)
        
        return vis_frame
    
    def set_theme(self, theme: VisualizationTheme) -> None:
        """设置可视化主题"""
        self.theme = theme
        self.detection_visualizer = DetectionVisualizer(theme)
        self.alert_visualizer = AlertVisualizer(theme)
        logger.info(f"切换可视化主题: {theme.value}")
    
    def clear_all(self) -> None:
        """清除所有可视化状态"""
        self.alert_visualizer.clear_alerts()
        logger.info("清除所有可视化状态")