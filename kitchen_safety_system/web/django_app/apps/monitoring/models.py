from django.db import models
from django.utils import timezone


class SystemStatus(models.Model):
    """系统状态记录"""
    
    STATUS_CHOICES = [
        ('running', '运行中'),
        ('stopped', '已停止'),
        ('error', '错误'),
        ('maintenance', '维护中'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='stopped',
        verbose_name='系统状态'
    )
    cpu_usage = models.FloatField(
        default=0.0,
        verbose_name='CPU使用率(%)'
    )
    memory_usage = models.FloatField(
        default=0.0,
        verbose_name='内存使用率(%)'
    )
    disk_usage = models.FloatField(
        default=0.0,
        verbose_name='磁盘使用率(%)'
    )
    detection_fps = models.FloatField(
        default=0.0,
        verbose_name='检测帧率(FPS)'
    )
    active_cameras = models.IntegerField(
        default=0,
        verbose_name='活跃摄像头数量'
    )
    last_detection_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后检测时间'
    )
    uptime_seconds = models.BigIntegerField(
        default=0,
        verbose_name='运行时间(秒)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='记录时间'
    )
    
    class Meta:
        verbose_name = '系统状态'
        verbose_name_plural = '系统状态'
        db_table = 'system_status'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"系统状态 - {self.get_status_display()} ({self.created_at})"
    
    @property
    def uptime_display(self):
        """格式化运行时间显示"""
        hours = self.uptime_seconds // 3600
        minutes = (self.uptime_seconds % 3600) // 60
        seconds = self.uptime_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class DetectionStatistics(models.Model):
    """检测统计信息"""
    
    date = models.DateField(
        default=timezone.now,
        verbose_name='统计日期'
    )
    total_detections = models.IntegerField(
        default=0,
        verbose_name='总检测次数'
    )
    person_detections = models.IntegerField(
        default=0,
        verbose_name='人员检测次数'
    )
    stove_detections = models.IntegerField(
        default=0,
        verbose_name='灶台检测次数'
    )
    fire_detections = models.IntegerField(
        default=0,
        verbose_name='火焰检测次数'
    )
    fall_alerts = models.IntegerField(
        default=0,
        verbose_name='跌倒报警次数'
    )
    unattended_alerts = models.IntegerField(
        default=0,
        verbose_name='无人看管报警次数'
    )
    false_positives = models.IntegerField(
        default=0,
        verbose_name='误报次数'
    )
    avg_detection_confidence = models.FloatField(
        default=0.0,
        verbose_name='平均检测置信度'
    )
    processing_time_ms = models.FloatField(
        default=0.0,
        verbose_name='平均处理时间(毫秒)'
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
        verbose_name = '检测统计'
        verbose_name_plural = '检测统计'
        db_table = 'detection_statistics'
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f"检测统计 - {self.date}"
    
    @property
    def total_alerts(self):
        return self.fall_alerts + self.unattended_alerts
    
    @property
    def alert_rate(self):
        if self.total_detections > 0:
            return (self.total_alerts / self.total_detections) * 100
        return 0.0


class PerformanceMetrics(models.Model):
    """性能指标记录"""
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='时间戳'
    )
    detection_latency_ms = models.FloatField(
        verbose_name='检测延迟(毫秒)'
    )
    frame_processing_time_ms = models.FloatField(
        verbose_name='帧处理时间(毫秒)'
    )
    queue_size = models.IntegerField(
        default=0,
        verbose_name='队列大小'
    )
    memory_usage_mb = models.FloatField(
        verbose_name='内存使用(MB)'
    )
    gpu_usage_percent = models.FloatField(
        default=0.0,
        verbose_name='GPU使用率(%)'
    )
    
    class Meta:
        verbose_name = '性能指标'
        verbose_name_plural = '性能指标'
        db_table = 'performance_metrics'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"性能指标 - {self.timestamp}"