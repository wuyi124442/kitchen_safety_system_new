from django.contrib import admin
from .models import SystemStatus, DetectionStatistics, PerformanceMetrics


@admin.register(SystemStatus)
class SystemStatusAdmin(admin.ModelAdmin):
    """系统状态管理"""
    list_display = ('status', 'cpu_usage', 'memory_usage', 'detection_fps', 'active_cameras', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('status',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('系统状态', {
            'fields': ('status', 'uptime_seconds', 'last_detection_time')
        }),
        ('性能指标', {
            'fields': ('cpu_usage', 'memory_usage', 'disk_usage', 'detection_fps')
        }),
        ('设备信息', {
            'fields': ('active_cameras',)
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )


@admin.register(DetectionStatistics)
class DetectionStatisticsAdmin(admin.ModelAdmin):
    """检测统计管理"""
    list_display = ('date', 'total_detections', 'fall_alerts', 'unattended_alerts', 'avg_detection_confidence')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('date',)
        }),
        ('检测统计', {
            'fields': ('total_detections', 'person_detections', 'stove_detections', 'fire_detections')
        }),
        ('报警统计', {
            'fields': ('fall_alerts', 'unattended_alerts', 'false_positives')
        }),
        ('性能指标', {
            'fields': ('avg_detection_confidence', 'processing_time_ms')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PerformanceMetrics)
class PerformanceMetricsAdmin(admin.ModelAdmin):
    """性能指标管理"""
    list_display = ('timestamp', 'detection_latency_ms', 'frame_processing_time_ms', 'queue_size', 'memory_usage_mb')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('性能指标', {
            'fields': ('detection_latency_ms', 'frame_processing_time_ms', 'queue_size')
        }),
        ('资源使用', {
            'fields': ('memory_usage_mb', 'gpu_usage_percent')
        }),
        ('时间信息', {
            'fields': ('timestamp',)
        }),
    )