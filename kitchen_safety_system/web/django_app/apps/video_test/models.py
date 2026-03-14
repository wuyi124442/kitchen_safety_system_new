from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class VideoUpload(models.Model):
    """视频上传记录"""
    
    STATUS_CHOICES = [
        ('uploaded', '已上传'),
        ('processing', '处理中'),
        ('completed', '处理完成'),
        ('failed', '处理失败'),
    ]
    
    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', blank=True)
    video_file = models.FileField('视频文件', upload_to='test_videos/%Y/%m/')
    thumbnail = models.ImageField('缩略图', upload_to='thumbnails/%Y/%m/', blank=True, null=True)
    
    # 处理状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='uploaded')
    progress = models.IntegerField('处理进度', default=0)  # 0-100
    
    # 检测结果
    total_frames = models.IntegerField('总帧数', default=0)
    processed_frames = models.IntegerField('已处理帧数', default=0)
    person_detections = models.IntegerField('人员检测次数', default=0)
    stove_detections = models.IntegerField('灶台检测次数', default=0)
    fire_detections = models.IntegerField('火焰检测次数', default=0)
    fall_events = models.IntegerField('跌倒事件', default=0)
    unattended_events = models.IntegerField('无人看管事件', default=0)
    
    # 结果文件
    result_video = models.FileField('结果视频', upload_to='results/%Y/%m/', blank=True, null=True)
    detection_log = models.TextField('检测日志', blank=True)
    
    # 元数据
    file_size = models.BigIntegerField('文件大小(字节)', default=0)
    duration = models.FloatField('视频时长(秒)', default=0.0)
    fps = models.FloatField('帧率', default=0.0)
    resolution = models.CharField('分辨率', max_length=20, blank=True)
    
    # 用户和时间
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='上传者')
    created_at = models.DateTimeField('上传时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    started_at = models.DateTimeField('开始处理时间', blank=True, null=True)
    completed_at = models.DateTimeField('完成时间', blank=True, null=True)
    
    class Meta:
        verbose_name = '视频上传'
        verbose_name_plural = '视频上传'
        db_table = 'video_uploads'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def processing_time(self):
        """处理时间"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return timezone.now() - self.started_at
        return None
    
    @property
    def file_size_mb(self):
        """文件大小(MB)"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0
    
    def start_processing(self):
        """开始处理"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save()
    
    def complete_processing(self):
        """完成处理"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress = 100
        self.save()
    
    def fail_processing(self, error_message):
        """处理失败"""
        self.status = 'failed'
        self.detection_log = error_message
        self.completed_at = timezone.now()
        self.save()


class DetectionResult(models.Model):
    """检测结果详情"""
    
    video_upload = models.ForeignKey(VideoUpload, on_delete=models.CASCADE, related_name='detection_results')
    frame_number = models.IntegerField('帧号')
    timestamp = models.FloatField('时间戳(秒)')
    
    # 检测结果
    persons = models.JSONField('人员检测', default=list)  # [{"bbox": [x1,y1,x2,y2], "confidence": 0.9}]
    stoves = models.JSONField('灶台检测', default=list)
    fires = models.JSONField('火焰检测', default=list)
    
    # 事件
    fall_detected = models.BooleanField('检测到跌倒', default=False)
    unattended_stove = models.BooleanField('无人看管灶台', default=False)
    
    # 置信度
    max_confidence = models.FloatField('最大置信度', default=0.0)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '检测结果'
        verbose_name_plural = '检测结果'
        db_table = 'detection_results'
        ordering = ['frame_number']
        indexes = [
            models.Index(fields=['video_upload', 'frame_number']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"Frame {self.frame_number} - {self.timestamp:.2f}s"