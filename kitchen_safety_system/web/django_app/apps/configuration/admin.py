from django.contrib import admin
from .models import SystemConfiguration, ConfigurationHistory, DetectionThreshold, CameraConfiguration


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """系统配置管理"""
    list_display = ('name', 'key', 'category', 'config_type', 'is_editable', 'updated_at')
    list_filter = ('category', 'config_type', 'is_editable')
    search_fields = ('name', 'key', 'description')
    ordering = ('category', 'display_order', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('key', 'name', 'category', 'config_type')
        }),
        ('配置值', {
            'fields': ('value', 'default_value')
        }),
        ('验证和显示', {
            'fields': ('validation_rules', 'is_editable', 'requires_restart', 'display_order')
        }),
        ('描述', {
            'fields': ('description',)
        }),
        ('更新信息', {
            'fields': ('updated_by', 'created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj and not obj.is_editable:
            readonly_fields.append('value')
        return readonly_fields


@admin.register(ConfigurationHistory)
class ConfigurationHistoryAdmin(admin.ModelAdmin):
    """配置变更历史管理"""
    list_display = ('configuration', 'changed_by', 'created_at')
    list_filter = ('created_at', 'changed_by')
    search_fields = ('configuration__name', 'configuration__key', 'change_reason')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('变更信息', {
            'fields': ('configuration', 'changed_by', 'change_reason')
        }),
        ('变更内容', {
            'fields': ('old_value', 'new_value')
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )


@admin.register(DetectionThreshold)
class DetectionThresholdAdmin(admin.ModelAdmin):
    """检测阈值管理"""
    list_display = ('name', 'detection_type', 'confidence_threshold', 'time_threshold_seconds', 'is_enabled')
    list_filter = ('detection_type', 'is_enabled')
    search_fields = ('name', 'detection_type', 'description')
    ordering = ('detection_type', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'detection_type', 'is_enabled')
        }),
        ('阈值配置', {
            'fields': ('confidence_threshold', 'time_threshold_seconds', 'distance_threshold_meters')
        }),
        ('附加参数', {
            'fields': ('additional_params',)
        }),
        ('描述', {
            'fields': ('description',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CameraConfiguration)
class CameraConfigurationAdmin(admin.ModelAdmin):
    """摄像头配置管理"""
    list_display = ('name', 'camera_id', 'location', 'resolution_display', 'fps', 'is_enabled')
    list_filter = ('location', 'is_enabled')
    search_fields = ('name', 'camera_id', 'location')
    ordering = ('location', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('camera_id', 'name', 'location', 'is_enabled')
        }),
        ('连接配置', {
            'fields': ('rtsp_url',)
        }),
        ('视频配置', {
            'fields': ('resolution_width', 'resolution_height', 'fps')
        }),
        ('检测配置', {
            'fields': ('detection_zones', 'calibration_data')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def resolution_display(self, obj):
        """显示分辨率"""
        return f"{obj.resolution_width}x{obj.resolution_height}"
    resolution_display.short_description = '分辨率'