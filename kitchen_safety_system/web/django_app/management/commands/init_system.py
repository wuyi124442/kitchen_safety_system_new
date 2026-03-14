from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from kitchen_safety_system.web.django_app.apps.configuration.models import (
    SystemConfiguration, DetectionThreshold, CameraConfiguration
)
from kitchen_safety_system.web.django_app.apps.alerts.models import AlertRule

User = get_user_model()


class Command(BaseCommand):
    help = '初始化厨房安全检测系统'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='管理员用户名 (默认: admin)'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='admin123',
            help='管理员密码 (默认: admin123)'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@kitchen-safety.com',
            help='管理员邮箱 (默认: admin@kitchen-safety.com)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始初始化厨房安全检测系统...'))
        
        # 创建管理员用户
        self.create_admin_user(options)
        
        # 初始化系统配置
        self.init_system_configurations()
        
        # 初始化检测阈值
        self.init_detection_thresholds()
        
        # 初始化报警规则
        self.init_alert_rules()
        
        # 初始化默认摄像头配置
        self.init_camera_configurations()
        
        self.stdout.write(self.style.SUCCESS('系统初始化完成！'))

    def create_admin_user(self, options):
        """创建管理员用户"""
        username = options['admin_username']
        password = options['admin_password']
        email = options['admin_email']
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'管理员用户 {username} 已存在')
            return
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'创建管理员用户: {username}'))

    def init_system_configurations(self):
        """初始化系统配置"""
        configs = [
            # 检测配置
            {
                'key': 'detection.fall_confidence_threshold',
                'name': '跌倒检测置信度阈值',
                'category': 'detection',
                'config_type': 'float',
                'value': '0.8',
                'default_value': '0.8',
                'description': '跌倒检测的最小置信度阈值',
                'validation_rules': {'min': 0.1, 'max': 1.0},
                'display_order': 1
            },
            {
                'key': 'detection.stove_distance_threshold',
                'name': '灶台距离阈值',
                'category': 'detection',
                'config_type': 'float',
                'value': '2.0',
                'default_value': '2.0',
                'description': '判断人员是否在灶台附近的距离阈值（米）',
                'validation_rules': {'min': 0.5, 'max': 10.0},
                'display_order': 2
            },
            {
                'key': 'detection.unattended_time_threshold',
                'name': '无人看管时间阈值',
                'category': 'detection',
                'config_type': 'integer',
                'value': '30',
                'default_value': '30',
                'description': '触发无人看管报警的时间阈值（秒）',
                'validation_rules': {'min': 5, 'max': 300},
                'display_order': 3
            },
            
            # 报警配置
            {
                'key': 'alert.email_enabled',
                'name': '启用邮件报警',
                'category': 'alert',
                'config_type': 'boolean',
                'value': 'true',
                'default_value': 'true',
                'description': '是否启用邮件报警通知',
                'display_order': 1
            },
            {
                'key': 'alert.sms_enabled',
                'name': '启用短信报警',
                'category': 'alert',
                'config_type': 'boolean',
                'value': 'false',
                'default_value': 'false',
                'description': '是否启用短信报警通知',
                'display_order': 2
            },
            {
                'key': 'alert.sound_enabled',
                'name': '启用声音报警',
                'category': 'alert',
                'config_type': 'boolean',
                'value': 'true',
                'default_value': 'true',
                'description': '是否启用声音报警',
                'display_order': 3
            },
            
            # 视频配置
            {
                'key': 'video.save_clips',
                'name': '保存视频片段',
                'category': 'video',
                'config_type': 'boolean',
                'value': 'true',
                'default_value': 'true',
                'description': '是否自动保存报警相关的视频片段',
                'display_order': 1
            },
            {
                'key': 'video.clip_duration',
                'name': '视频片段时长',
                'category': 'video',
                'config_type': 'integer',
                'value': '10',
                'default_value': '10',
                'description': '保存的视频片段时长（秒）',
                'validation_rules': {'min': 5, 'max': 60},
                'display_order': 2
            },
            {
                'key': 'video.max_storage_days',
                'name': '视频保存天数',
                'category': 'video',
                'config_type': 'integer',
                'value': '30',
                'default_value': '30',
                'description': '视频文件最大保存天数',
                'validation_rules': {'min': 1, 'max': 365},
                'display_order': 3
            },
            
            # 性能配置
            {
                'key': 'performance.max_fps',
                'name': '最大处理帧率',
                'category': 'performance',
                'config_type': 'integer',
                'value': '30',
                'default_value': '30',
                'description': '视频处理的最大帧率',
                'validation_rules': {'min': 1, 'max': 60},
                'display_order': 1
            },
            {
                'key': 'performance.queue_size',
                'name': '处理队列大小',
                'category': 'performance',
                'config_type': 'integer',
                'value': '100',
                'default_value': '100',
                'description': '视频帧处理队列的最大大小',
                'validation_rules': {'min': 10, 'max': 1000},
                'display_order': 2
            }
        ]
        
        for config_data in configs:
            config, created = SystemConfiguration.objects.get_or_create(
                key=config_data['key'],
                defaults=config_data
            )
            if created:
                self.stdout.write(f'创建系统配置: {config.name}')

    def init_detection_thresholds(self):
        """初始化检测阈值"""
        thresholds = [
            {
                'name': '跌倒检测阈值',
                'detection_type': 'fall_detection',
                'confidence_threshold': 0.8,
                'time_threshold_seconds': 3,
                'distance_threshold_meters': 0.0,
                'additional_params': {
                    'angle_threshold': 45,
                    'velocity_threshold': 2.0
                },
                'description': '人员跌倒检测的相关阈值配置'
            },
            {
                'name': '无人看管检测阈值',
                'detection_type': 'unattended_stove',
                'confidence_threshold': 0.7,
                'time_threshold_seconds': 30,
                'distance_threshold_meters': 2.0,
                'additional_params': {
                    'fire_confidence': 0.8,
                    'person_confidence': 0.7
                },
                'description': '灶台无人看管检测的相关阈值配置'
            }
        ]
        
        for threshold_data in thresholds:
            threshold, created = DetectionThreshold.objects.get_or_create(
                name=threshold_data['name'],
                defaults=threshold_data
            )
            if created:
                self.stdout.write(f'创建检测阈值: {threshold.name}')

    def init_alert_rules(self):
        """初始化报警规则"""
        rules = [
            {
                'name': '跌倒报警规则',
                'alert_type': 'fall',
                'threshold_config': {
                    'confidence_threshold': 0.8,
                    'duration_seconds': 3
                },
                'notification_config': {
                    'email': True,
                    'sms': False,
                    'sound': True,
                    'webhook': False
                },
                'cooldown_seconds': 60,
                'description': '检测到人员跌倒时触发的报警规则'
            },
            {
                'name': '无人看管报警规则',
                'alert_type': 'unattended_stove',
                'threshold_config': {
                    'confidence_threshold': 0.7,
                    'duration_seconds': 30,
                    'distance_meters': 2.0
                },
                'notification_config': {
                    'email': True,
                    'sms': True,
                    'sound': True,
                    'webhook': False
                },
                'cooldown_seconds': 120,
                'description': '检测到灶台无人看管时触发的报警规则'
            }
        ]
        
        for rule_data in rules:
            rule, created = AlertRule.objects.get_or_create(
                name=rule_data['name'],
                defaults=rule_data
            )
            if created:
                self.stdout.write(f'创建报警规则: {rule.name}')

    def init_camera_configurations(self):
        """初始化摄像头配置"""
        cameras = [
            {
                'camera_id': 'camera_01',
                'name': '厨房主摄像头',
                'location': '厨房中央',
                'rtsp_url': 'rtsp://192.168.1.100:554/stream1',
                'resolution_width': 1920,
                'resolution_height': 1080,
                'fps': 30,
                'detection_zones': [
                    {
                        'name': '灶台区域',
                        'points': [[100, 100], [500, 100], [500, 400], [100, 400]]
                    },
                    {
                        'name': '操作区域',
                        'points': [[600, 200], [1000, 200], [1000, 600], [600, 600]]
                    }
                ],
                'calibration_data': {
                    'scale_factor': 1.0,
                    'offset_x': 0,
                    'offset_y': 0,
                    'pixels_per_meter': 100
                }
            }
        ]
        
        for camera_data in cameras:
            camera, created = CameraConfiguration.objects.get_or_create(
                camera_id=camera_data['camera_id'],
                defaults=camera_data
            )
            if created:
                self.stdout.write(f'创建摄像头配置: {camera.name}')

        self.stdout.write(self.style.SUCCESS('系统初始化完成！'))
        self.stdout.write('默认管理员账户信息:')
        self.stdout.write(f'  用户名: {options.get("admin_username", "admin")}')
        self.stdout.write(f'  密码: {options.get("admin_password", "admin123")}')
        self.stdout.write('请访问 /admin/ 或 /dashboard/ 开始使用系统')