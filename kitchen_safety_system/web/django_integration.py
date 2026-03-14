"""
Django集成模块 - 连接Django后台与检测系统
"""

import os
import sys
import django
from django.conf import settings
from pathlib import Path
import logging

# 添加Django项目路径到Python路径
BASE_DIR = Path(__file__).resolve().parent.parent
DJANGO_APP_PATH = BASE_DIR / 'kitchen_safety_system' / 'web' / 'django_app'
sys.path.insert(0, str(DJANGO_APP_PATH))

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings')

# 初始化Django
django.setup()

# 导入Django模型
from kitchen_safety_system.web.django_app.apps.alerts.models import Alert, NotificationLog
from kitchen_safety_system.web.django_app.apps.monitoring.models import SystemStatus, DetectionStatistics, PerformanceMetrics
from kitchen_safety_system.web.django_app.apps.configuration.models import SystemConfiguration, DetectionThreshold, CameraConfiguration
from kitchen_safety_system.web.django_app.apps.authentication.models import User

logger = logging.getLogger(__name__)


class DjangoIntegration:
    """Django集成类 - 提供与Django后台的接口"""
    
    def __init__(self):
        self.logger = logger
    
    # 报警管理
    def create_alert(self, alert_type, title, description, **kwargs):
        """创建报警记录"""
        try:
            alert = Alert.objects.create(
                alert_type=alert_type,
                title=title,
                description=description,
                severity=kwargs.get('severity', 'medium'),
                location=kwargs.get('location'),
                camera_id=kwargs.get('camera_id'),
                detection_confidence=kwargs.get('confidence', 0.0),
                video_clip_path=kwargs.get('video_clip_path'),
                screenshot_path=kwargs.get('screenshot_path'),
                metadata=kwargs.get('metadata', {})
            )
            self.logger.info(f"创建报警记录: {alert.id} - {title}")
            return alert
        except Exception as e:
            self.logger.error(f"创建报警记录失败: {e}")
            return None
    
    def get_active_alerts(self):
        """获取活跃的报警"""
        try:
            return Alert.objects.filter(status='active').order_by('-created_at')
        except Exception as e:
            self.logger.error(f"获取活跃报警失败: {e}")
            return []
    
    def acknowledge_alert(self, alert_id, user_name):
        """确认报警"""
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.acknowledge(user_name)
            self.logger.info(f"报警已确认: {alert_id} by {user_name}")
            return True
        except Alert.DoesNotExist:
            self.logger.error(f"报警不存在: {alert_id}")
            return False
        except Exception as e:
            self.logger.error(f"确认报警失败: {e}")
            return False
    
    # 系统状态管理
    def update_system_status(self, status_data):
        """更新系统状态"""
        try:
            SystemStatus.objects.create(**status_data)
            self.logger.debug("系统状态已更新")
            return True
        except Exception as e:
            self.logger.error(f"更新系统状态失败: {e}")
            return False
    
    def get_latest_system_status(self):
        """获取最新系统状态"""
        try:
            return SystemStatus.objects.first()
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            return None
    
    # 检测统计管理
    def update_detection_statistics(self, date, stats_data):
        """更新检测统计"""
        try:
            stats, created = DetectionStatistics.objects.get_or_create(
                date=date,
                defaults=stats_data
            )
            if not created:
                # 更新现有记录
                for key, value in stats_data.items():
                    setattr(stats, key, value)
                stats.save()
            
            self.logger.debug(f"检测统计已更新: {date}")
            return stats
        except Exception as e:
            self.logger.error(f"更新检测统计失败: {e}")
            return None
    
    def record_performance_metrics(self, metrics_data):
        """记录性能指标"""
        try:
            PerformanceMetrics.objects.create(**metrics_data)
            self.logger.debug("性能指标已记录")
            return True
        except Exception as e:
            self.logger.error(f"记录性能指标失败: {e}")
            return False
    
    # 配置管理
    def get_system_configuration(self, key=None):
        """获取系统配置"""
        try:
            if key:
                config = SystemConfiguration.objects.get(key=key)
                return config.get_typed_value()
            else:
                configs = {}
                for config in SystemConfiguration.objects.all():
                    configs[config.key] = config.get_typed_value()
                return configs
        except SystemConfiguration.DoesNotExist:
            self.logger.warning(f"配置不存在: {key}")
            return None
        except Exception as e:
            self.logger.error(f"获取系统配置失败: {e}")
            return None
    
    def get_detection_thresholds(self):
        """获取检测阈值"""
        try:
            thresholds = {}
            for threshold in DetectionThreshold.objects.filter(is_enabled=True):
                thresholds[threshold.name] = {
                    'detection_type': threshold.detection_type,
                    'confidence_threshold': threshold.confidence_threshold,
                    'time_threshold_seconds': threshold.time_threshold_seconds,
                    'distance_threshold_meters': threshold.distance_threshold_meters,
                    'additional_params': threshold.additional_params
                }
            return thresholds
        except Exception as e:
            self.logger.error(f"获取检测阈值失败: {e}")
            return {}
    
    def get_camera_configurations(self):
        """获取摄像头配置"""
        try:
            cameras = []
            for camera in CameraConfiguration.objects.filter(is_enabled=True):
                cameras.append({
                    'camera_id': camera.camera_id,
                    'name': camera.name,
                    'location': camera.location,
                    'rtsp_url': camera.rtsp_url,
                    'resolution_width': camera.resolution_width,
                    'resolution_height': camera.resolution_height,
                    'fps': camera.fps,
                    'detection_zones': camera.detection_zones,
                    'calibration_data': camera.calibration_data
                })
            return cameras
        except Exception as e:
            self.logger.error(f"获取摄像头配置失败: {e}")
            return []
    
    # 通知管理
    def create_notification_log(self, alert_id, channel, recipient, message_content):
        """创建通知日志"""
        try:
            alert = Alert.objects.get(id=alert_id)
            notification = NotificationLog.objects.create(
                alert=alert,
                channel=channel,
                recipient=recipient,
                message_content=message_content
            )
            self.logger.info(f"创建通知日志: {notification.id}")
            return notification
        except Alert.DoesNotExist:
            self.logger.error(f"报警不存在: {alert_id}")
            return None
        except Exception as e:
            self.logger.error(f"创建通知日志失败: {e}")
            return None
    
    def update_notification_status(self, notification_id, status, error_message=None):
        """更新通知状态"""
        try:
            notification = NotificationLog.objects.get(id=notification_id)
            notification.status = status
            if error_message:
                notification.error_message = error_message
            if status == 'sent':
                from django.utils import timezone
                notification.sent_at = timezone.now()
            notification.save()
            
            self.logger.debug(f"通知状态已更新: {notification_id} -> {status}")
            return True
        except NotificationLog.DoesNotExist:
            self.logger.error(f"通知日志不存在: {notification_id}")
            return False
        except Exception as e:
            self.logger.error(f"更新通知状态失败: {e}")
            return False
    
    # 用户管理
    def get_notification_recipients(self, notification_type='email'):
        """获取通知接收者列表"""
        try:
            users = User.objects.filter(is_active=True)
            recipients = []
            
            for user in users:
                profile = getattr(user, 'profile', None)
                if profile:
                    if notification_type == 'email' and profile.notification_email and user.email:
                        recipients.append(user.email)
                    elif notification_type == 'sms' and profile.notification_sms and user.phone:
                        recipients.append(user.phone)
                else:
                    # 如果没有配置文件，默认发送邮件通知
                    if notification_type == 'email' and user.email:
                        recipients.append(user.email)
            
            return recipients
        except Exception as e:
            self.logger.error(f"获取通知接收者失败: {e}")
            return []
    
    # 数据清理
    def cleanup_old_data(self, days=30):
        """清理旧数据"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # 清理旧的系统状态记录
            old_status_count = SystemStatus.objects.filter(created_at__lt=cutoff_date).count()
            SystemStatus.objects.filter(created_at__lt=cutoff_date).delete()
            
            # 清理旧的性能指标记录
            old_metrics_count = PerformanceMetrics.objects.filter(timestamp__lt=cutoff_date).count()
            PerformanceMetrics.objects.filter(timestamp__lt=cutoff_date).delete()
            
            # 清理已解决的旧报警记录
            old_alerts_count = Alert.objects.filter(
                status='resolved',
                resolved_at__lt=cutoff_date
            ).count()
            Alert.objects.filter(
                status='resolved',
                resolved_at__lt=cutoff_date
            ).delete()
            
            self.logger.info(f"数据清理完成: 状态记录 {old_status_count}, 性能指标 {old_metrics_count}, 报警记录 {old_alerts_count}")
            return True
            
        except Exception as e:
            self.logger.error(f"数据清理失败: {e}")
            return False


# 全局Django集成实例
django_integration = DjangoIntegration()