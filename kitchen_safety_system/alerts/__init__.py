"""
报警管理模块

提供多种报警方式支持、报警去重和频率控制功能。
"""

from .alert_manager import AlertManager
from .notification_channels import (
    NotificationChannel,
    SoundNotificationChannel,
    EmailNotificationChannel,
    SMSNotificationChannel,
    ConsoleNotificationChannel
)

__all__ = [
    'AlertManager',
    'NotificationChannel',
    'SoundNotificationChannel',
    'EmailNotificationChannel', 
    'SMSNotificationChannel',
    'ConsoleNotificationChannel'
]