from django.contrib import admin
from .models import Alert, AlertRule, NotificationLog


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """报警记录管理"""
    list_display = ('title', 'alert_type', 'severity', 'status', 'location', 'created_at')
    list_filter = ('alert_type', 'severity', 'status', 'created_at')
    search_fields = ('title', 'description', 'location', 'camera_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('alert_type', 'severity', 'status', 'title', 'description')
        }),
        ('位置信息', {
            'fields': ('location', 'camera_id')
        }),
        ('检测信息', {
            'fields': ('detection_confidence', 'video_clip_path', 'screenshot_path', 'metadata')
        }),
        ('处理信息', {
            'fields': ('acknowledged_by', 'acknowledged_at', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_acknowledged', 'mark_as_resolved', 'mark_as_false_positive']
    
    def mark_as_acknowledged(self, request, queryset):
        """批量确认报警"""
        count = 0
        for alert in queryset.filter(status='active'):
            alert.acknowledge(request.user.username)
            count += 1
        self.message_user(request, f'已确认 {count} 个报警')
    mark_as_acknowledged.short_description = '确认选中的报警'
    
    def mark_as_resolved(self, request, queryset):
        """批量解决报警"""
        count = 0
        for alert in queryset.filter(status__in=['active', 'acknowledged']):
            alert.resolve(request.user.username, '批量解决')
            count += 1
        self.message_user(request, f'已解决 {count} 个报警')
    mark_as_resolved.short_description = '解决选中的报警'
    
    def mark_as_false_positive(self, request, queryset):
        """批量标记为误报"""
        count = 0
        for alert in queryset.filter(status__in=['active', 'acknowledged']):
            alert.mark_false_positive(request.user.username)
            count += 1
        self.message_user(request, f'已标记 {count} 个报警为误报')
    mark_as_false_positive.short_description = '标记选中的报警为误报'


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    """报警规则管理"""
    list_display = ('name', 'alert_type', 'is_enabled', 'cooldown_seconds', 'created_at')
    list_filter = ('alert_type', 'is_enabled', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'alert_type', 'is_enabled', 'description')
        }),
        ('阈值配置', {
            'fields': ('threshold_config',)
        }),
        ('通知配置', {
            'fields': ('notification_config', 'cooldown_seconds')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """通知日志管理"""
    list_display = ('alert', 'channel', 'recipient', 'status', 'retry_count', 'created_at')
    list_filter = ('channel', 'status', 'created_at')
    search_fields = ('recipient', 'message_content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('通知信息', {
            'fields': ('alert', 'channel', 'recipient', 'status')
        }),
        ('消息内容', {
            'fields': ('message_content', 'error_message')
        }),
        ('发送信息', {
            'fields': ('retry_count', 'sent_at', 'created_at')
        }),
    )