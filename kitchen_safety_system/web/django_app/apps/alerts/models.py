from django.db import models
from django.utils import timezone


class Alert(models.Model):
    """报警记录模型"""
    
    ALERT_TYPE_CHOICES = [
        ('fall', '跌倒报警'),
        ('unattended_stove', '无人看管灶台'),
        ('system_error', '系统错误'),
        ('camera_offline', '摄像头离线'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '严重'),
    ]
    
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('acknowledged', '已确认'),
        ('resolved', '已解决'),
        ('false_positive', '误报'),
    ]
    
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPE_CHOICES,
        verbose_name='报警类型'
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='medium',
        verbose_name='严重程度'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='状态'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='标题'
    )
    description = models.TextField(
        verbose_name='描述'
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='位置'
    )
    camera_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='摄像头ID'
    )
    detection_confidence = models.FloatField(
        default=0.0,
        verbose_name='检测置信度'
    )
    video_clip_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='视频片段路径'
    )
    screenshot_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='截图路径'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='元数据'
    )
    acknowledged_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='确认人'
    )
    acknowledged_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='确认时间'
    )
    resolved_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='解决人'
    )
    resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='解决时间'
    )
    resolution_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='解决备注'
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
        verbose_name = '报警记录'
        verbose_name_plural = '报警记录'
        db_table = 'alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.title} ({self.created_at})"
    
    @property
    def duration(self):
        """报警持续时间"""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return timezone.now() - self.created_at
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_resolved(self):
        return self.status == 'resolved'
    
    def acknowledge(self, user):
        """确认报警"""
        if self.status == 'active':
            self.status = 'acknowledged'
            self.acknowledged_by = user
            self.acknowledged_at = timezone.now()
            self.save()
    
    def resolve(self, user, notes=None):
        """解决报警"""
        if self.status in ['active', 'acknowledged']:
            self.status = 'resolved'
            self.resolved_by = user
            self.resolved_at = timezone.now()
            if notes:
                self.resolution_notes = notes
            self.save()
    
    def mark_false_positive(self, user):
        """标记为误报"""
        self.status = 'false_positive'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = '标记为误报'
        self.save()


class AlertRule(models.Model):
    """报警规则配置"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='规则名称'
    )
    alert_type = models.CharField(
        max_length=20,
        choices=Alert.ALERT_TYPE_CHOICES,
        verbose_name='报警类型'
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name='启用状态'
    )
    threshold_config = models.JSONField(
        default=dict,
        verbose_name='阈值配置'
    )
    notification_config = models.JSONField(
        default=dict,
        verbose_name='通知配置'
    )
    cooldown_seconds = models.IntegerField(
        default=60,
        verbose_name='冷却时间(秒)'
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
        verbose_name = '报警规则'
        verbose_name_plural = '报警规则'
        db_table = 'alert_rules'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_alert_type_display()})"


class NotificationLog(models.Model):
    """通知发送日志"""
    
    CHANNEL_CHOICES = [
        ('email', '邮件'),
        ('sms', '短信'),
        ('webhook', 'Webhook'),
        ('sound', '声音'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待发送'),
        ('sent', '已发送'),
        ('failed', '发送失败'),
        ('retry', '重试中'),
    ]
    
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='关联报警'
    )
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        verbose_name='通知渠道'
    )
    recipient = models.CharField(
        max_length=200,
        verbose_name='接收者'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='发送状态'
    )
    message_content = models.TextField(
        verbose_name='消息内容'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='错误信息'
    )
    retry_count = models.IntegerField(
        default=0,
        verbose_name='重试次数'
    )
    sent_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='发送时间'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    
    class Meta:
        verbose_name = '通知日志'
        verbose_name_plural = '通知日志'
        db_table = 'notification_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_channel_display()} - {self.recipient} ({self.get_status_display()})"