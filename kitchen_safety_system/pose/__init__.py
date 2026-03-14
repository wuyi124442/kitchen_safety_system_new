"""
姿态识别模块

提供基于MediaPipe的人体姿态检测和跌倒识别功能。
"""

from .pose_analyzer import PoseAnalyzer

__all__ = [
    'PoseAnalyzer'
]