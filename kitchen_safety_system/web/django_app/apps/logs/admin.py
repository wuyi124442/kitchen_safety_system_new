from django.contrib import admin
from .models import LogEntry


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """日志条目管理"""
    
    list_display = ['id', 'timestamp', 'level', 'log_type', 'message_preview', 'module', 'user']
    list_filter = ['level', 'log_type', 'timestamp', 'module']
    search_fields = ['message', 'module', 'function']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def message_preview(self, obj):
        """消息预览"""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = '消息预览'
    
    def has_add_permission(self, request):
        """禁止手动添加日志"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """禁止修改日志"""
        return False