"""
检测模块

提供YOLO目标检测和MediaPipe姿态检测功能。
"""

from .yolo_detector import YOLODetector
from ..pose.pose_analyzer import PoseAnalyzer

# 这些模块将在后续任务中实现
# from .detection_system import DetectionSystem

__all__ = [
    'YOLODetector',
    'PoseAnalyzer', 
    # 'DetectionSystem'
]