from rest_framework import serializers
from .models import LogEntry


class LogEntrySerializer(serializers.ModelSerializer):
    """日志条目序列化器"""
    
    class Meta:
        model = LogEntry
        fields = [
            'id', 'level', 'log_type', 'message', 'timestamp',
            'module', 'function', 'line_number', 'additional_data', 'user'
        ]
        read_only_fields = ['id', 'timestamp']


class LogQuerySerializer(serializers.Serializer):
    """日志查询参数序列化器"""
    
    start_date = serializers.DateTimeField(required=False, help_text='开始时间')
    end_date = serializers.DateTimeField(required=False, help_text='结束时间')
    level = serializers.ChoiceField(
        choices=LogEntry.LEVEL_CHOICES,
        required=False,
        help_text='日志级别'
    )
    log_type = serializers.ChoiceField(
        choices=LogEntry.TYPE_CHOICES,
        required=False,
        help_text='日志类型'
    )
    search = serializers.CharField(required=False, help_text='搜索关键词')
    page = serializers.IntegerField(default=1, min_value=1, help_text='页码')
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100, help_text='每页数量')


class LogExportSerializer(serializers.Serializer):
    """日志导出参数序列化器"""
    
    start_date = serializers.DateTimeField(required=False, help_text='开始时间')
    end_date = serializers.DateTimeField(required=False, help_text='结束时间')
    level = serializers.ChoiceField(
        choices=LogEntry.LEVEL_CHOICES,
        required=False,
        help_text='日志级别'
    )
    log_type = serializers.ChoiceField(
        choices=LogEntry.TYPE_CHOICES,
        required=False,
        help_text='日志类型'
    )
    format = serializers.ChoiceField(
        choices=[('csv', 'CSV'), ('json', 'JSON'), ('txt', 'TXT')],
        default='csv',
        help_text='导出格式'
    )