from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class SystemConfiguration(models.Model):
    """系统配置模型"""
    
    CONFIG_CATEGORY_CHOICES = [
        ('detection', '检测配置'),
        ('alert', '报警配置'),
        ('video', '视频配置'),
        ('notification', '通知配置'),
        ('performance', '性能配置'),
        ('system', '系统配置'),
    ]
    
    CONFIG_TYPE_CHOICES = [
        ('string', '字符串'),
        ('integer', '整数'),
        ('float', '浮点数'),
        ('boolean', '布尔值'),
        ('json', 'JSON对象'),
    ]
    
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='配置键'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='配置名称'
    )
    category = models.CharField(
        max_length=20,
        choices=CONFIG_CATEGORY_CHOICES,
        verbose_name='配置分类'
    )
    config_type = models.CharField(
        max_length=20,
        choices=CONFIG_TYPE_CHOICES,
        verbose_name='配置类型'
    )
    value = models.TextField(
        verbose_name='配置值'
    )
    default_value = models.TextField(
        verbose_name='默认值'
    )
    description = models.TextField(
        blank=True,
        verbose_name='描述'
    )
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='验证规则'
    )
    is_editable = models.BooleanField(
        default=True,
        verbose_name='可编辑'
    )
    requires_restart = models.BooleanField(
        default=False,
        verbose_name='需要重启'
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name='显示顺序'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    updated_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='更新人'
    )
    
    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'
        db_table = 'system_configurations'
        ordering = ['category', 'display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.key})"
    
    def get_typed_value(self):
        """获取类型化的配置值"""
        if self.config_type == 'integer':
            return int(self.value)
        elif self.config_type == 'float':
            return float(self.value)
        elif self.config_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.config_type == 'json':
            import json
            return json.loads(self.value)
        else:
            return self.value
    
    def set_typed_value(self, value):
        """设置类型化的配置值"""
        if self.config_type == 'json':
            import json
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)
    
    def validate_value(self, value):
        """验证配置值"""
        rules = self.validation_rules
        
        if self.config_type == 'integer':
            try:
                int_value = int(value)
                if 'min' in rules and int_value < rules['min']:
                    return False, f"值不能小于 {rules['min']}"
                if 'max' in rules and int_value > rules['max']:
                    return False, f"值不能大于 {rules['max']}"
            except ValueError:
                return False, "必须是整数"
        
        elif self.config_type == 'float':
            try:
                float_value = float(value)
                if 'min' in rules and float_value < rules['min']:
                    return False, f"值不能小于 {rules['min']}"
                if 'max' in rules and float_value > rules['max']:
                    return False, f"值不能大于 {rules['max']}"
            except ValueError:
                return False, "必须是数字"
        
        elif self.config_type == 'json':
            try:
                import json
                json.loads(value)
            except json.JSONDecodeError:
                return False, "必须是有效的JSON格式"
        
        return True, ""


class ConfigurationHistory(models.Model):
    """配置变更历史"""
    
    configuration = models.ForeignKey(
        SystemConfiguration,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='配置项'
    )
    old_value = models.TextField(
        verbose_name='旧值'
    )
    new_value = models.TextField(
        verbose_name='新值'
    )
    changed_by = models.CharField(
        max_length=100,
        verbose_name='修改人'
    )
    change_reason = models.TextField(
        blank=True,
        verbose_name='修改原因'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='修改时间'
    )
    
    class Meta:
        verbose_name = '配置变更历史'
        verbose_name_plural = '配置变更历史'
        db_table = 'configuration_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.configuration.name} - {self.created_at}"


class DetectionThreshold(models.Model):
    """检测阈值配置"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='阈值名称'
    )
    detection_type = models.CharField(
        max_length=50,
        verbose_name='检测类型'
    )
    confidence_threshold = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.8,
        verbose_name='置信度阈值'
    )
    time_threshold_seconds = models.IntegerField(
        validators=[MinValueValidator(1)],
        default=30,
        verbose_name='时间阈值(秒)'
    )
    distance_threshold_meters = models.FloatField(
        validators=[MinValueValidator(0.1)],
        default=2.0,
        verbose_name='距离阈值(米)'
    )
    additional_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='附加参数'
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name='启用状态'
    )
    description = models.TextField(
        blank=True,
        verbose_name='描述'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        verbose_name = '检测阈值'
        verbose_name_plural = '检测阈值'
        db_table = 'detection_thresholds'
        ordering = ['detection_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.detection_type})"


class CameraConfiguration(models.Model):
    """摄像头配置"""
    
    camera_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='摄像头ID'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='摄像头名称'
    )
    location = models.CharField(
        max_length=100,
        verbose_name='安装位置'
    )
    rtsp_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='RTSP地址'
    )
    resolution_width = models.IntegerField(
        default=1920,
        verbose_name='分辨率宽度'
    )
    resolution_height = models.IntegerField(
        default=1080,
        verbose_name='分辨率高度'
    )
    fps = models.IntegerField(
        default=30,
        verbose_name='帧率'
    )
    detection_zones = models.JSONField(
        default=list,
        blank=True,
        verbose_name='检测区域'
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name='启用状态'
    )
    calibration_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='标定数据'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        verbose_name = '摄像头配置'
        verbose_name_plural = '摄像头配置'
        db_table = 'camera_configurations'
        ordering = ['location', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.location})"