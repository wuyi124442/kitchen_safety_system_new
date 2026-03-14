from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class LogEntry(models.Model):
    """日志条目模型"""
    
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    TYPE_CHOICES = [
        ('SYSTEM', '系统日志'),
        ('DETECTION', '检测日志'),
        ('ALERT', '报警日志'),
        ('USER', '用户操作日志'),
        ('ERROR', '错误日志'),
    ]
    
    level = models.CharField('日志级别', max_length=10, choices=LEVEL_CHOICES, default='INFO')
    log_type = models.CharField('日志类型', max_length=20, choices=TYPE_CHOICES, default='SYSTEM')
    message = models.TextField('日志消息')
    timestamp = models.DateTimeField('时间戳', auto_now_add=True)
    module = models.CharField('模块', max_length=100, blank=True, null=True)
    function = models.CharField('函数', max_length=100, blank=True, null=True)
    line_number = models.IntegerField('行号', blank=True, null=True)
    additional_data = models.JSONField('附加数据', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                            verbose_name='用户', related_name='custom_log_entries')
    
    class Meta:
        db_table = 'log_entries'
        verbose_name = '日志条目'
        verbose_name_plural = '日志条目'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['level']),
            models.Index(fields=['log_type']),
            models.Index(fields=['timestamp', 'level']),
            models.Index(fields=['timestamp', 'log_type']),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.message[:50]}"