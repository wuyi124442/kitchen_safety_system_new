import csv
import json
from datetime import datetime, timedelta
from django.http import HttpResponse, StreamingHttpResponse
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import LogEntry
from .serializers import LogEntrySerializer, LogQuerySerializer, LogExportSerializer


class LogPagination(PageNumberPagination):
    """日志分页器"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def log_list(request):
    """
    获取日志列表
    支持按时间、类型、严重程度查询
    """
    serializer = LogQuerySerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    queryset = LogEntry.objects.all()
    
    # 时间范围过滤
    if data.get('start_date'):
        queryset = queryset.filter(timestamp__gte=data['start_date'])
    if data.get('end_date'):
        queryset = queryset.filter(timestamp__lte=data['end_date'])
    
    # 日志级别过滤
    if data.get('level'):
        queryset = queryset.filter(level=data['level'])
    
    # 日志类型过滤
    if data.get('log_type'):
        queryset = queryset.filter(log_type=data['log_type'])
    
    # 关键词搜索
    if data.get('search'):
        search_term = data['search']
        queryset = queryset.filter(
            Q(message__icontains=search_term) |
            Q(module__icontains=search_term) |
            Q(function__icontains=search_term)
        )
    
    # 分页
    paginator = LogPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = LogEntrySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    serializer = LogEntrySerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def log_detail(request, log_id):
    """获取日志详情"""
    try:
        log_entry = LogEntry.objects.get(id=log_id)
        serializer = LogEntrySerializer(log_entry)
        return Response(serializer.data)
    except LogEntry.DoesNotExist:
        return Response(
            {'error': '日志记录不存在'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def log_export(request):
    """
    导出日志
    支持CSV、JSON、TXT格式
    """
    serializer = LogExportSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    queryset = LogEntry.objects.all()
    
    # 应用过滤条件
    if data.get('start_date'):
        queryset = queryset.filter(timestamp__gte=data['start_date'])
    if data.get('end_date'):
        queryset = queryset.filter(timestamp__lte=data['end_date'])
    if data.get('level'):
        queryset = queryset.filter(level=data['level'])
    if data.get('log_type'):
        queryset = queryset.filter(log_type=data['log_type'])
    
    export_format = data.get('format', 'csv')
    
    if export_format == 'csv':
        return export_csv(queryset)
    elif export_format == 'json':
        return export_json(queryset)
    elif export_format == 'txt':
        return export_txt(queryset)
    else:
        return Response(
            {'error': '不支持的导出格式'},
            status=status.HTTP_400_BAD_REQUEST
        )


def export_csv(queryset):
    """导出CSV格式"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # 添加BOM以支持中文
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', '时间', '级别', '类型', '消息', '模块', '函数', '行号', '用户'
    ])
    
    for log in queryset:
        writer.writerow([
            log.id,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.get_level_display(),
            log.get_log_type_display(),
            log.message,
            log.module or '',
            log.function or '',
            log.line_number or '',
            log.user.username if log.user else ''
        ])
    
    return response


def export_json(queryset):
    """导出JSON格式"""
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    logs_data = []
    for log in queryset:
        logs_data.append({
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'level': log.level,
            'log_type': log.log_type,
            'message': log.message,
            'module': log.module,
            'function': log.function,
            'line_number': log.line_number,
            'additional_data': log.additional_data,
            'user': log.user.username if log.user else None
        })
    
    response.write(json.dumps(logs_data, ensure_ascii=False, indent=2))
    return response


def export_txt(queryset):
    """导出TXT格式"""
    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt"'
    
    for log in queryset:
        line = f"[{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [{log.level}] [{log.log_type}] {log.message}"
        if log.module:
            line += f" - {log.module}"
        if log.function:
            line += f".{log.function}"
        if log.line_number:
            line += f":{log.line_number}"
        if log.user:
            line += f" (用户: {log.user.username})"
        line += "\n"
        response.write(line)
    
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def log_statistics(request):
    """获取日志统计信息"""
    # 最近7天的统计
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    queryset = LogEntry.objects.filter(timestamp__gte=start_date)
    
    # 按级别统计
    level_stats = {}
    for choice in LogEntry.LEVEL_CHOICES:
        level = choice[0]
        count = queryset.filter(level=level).count()
        level_stats[level] = count
    
    # 按类型统计
    type_stats = {}
    for choice in LogEntry.TYPE_CHOICES:
        log_type = choice[0]
        count = queryset.filter(log_type=log_type).count()
        type_stats[log_type] = count
    
    # 按天统计
    daily_stats = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = queryset.filter(
            timestamp__gte=day_start,
            timestamp__lt=day_end
        ).count()
        
        daily_stats.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': count
        })
    
    return Response({
        'total_logs': queryset.count(),
        'level_statistics': level_stats,
        'type_statistics': type_stats,
        'daily_statistics': daily_stats,
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    })


# Web界面视图
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET"])
def log_query_page(request):
    """日志查询页面"""
    context = {
        'title': '日志查询',
        'level_choices': LogEntry.LEVEL_CHOICES,
        'type_choices': LogEntry.TYPE_CHOICES,
    }
    return render(request, 'logs/log_query.html', context)


@login_required
@require_http_methods(["GET"])
def log_monitor_page(request):
    """实时日志监控页面"""
    context = {
        'title': '实时日志监控',
        'level_choices': LogEntry.LEVEL_CHOICES,
        'type_choices': LogEntry.TYPE_CHOICES,
    }
    return render(request, 'logs/log_monitor.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def log_realtime(request):
    """实时日志接口 - 获取最新日志"""
    # 获取最近5分钟的日志
    since = datetime.now() - timedelta(minutes=5)
    
    # 获取查询参数
    last_id = request.GET.get('last_id', 0)
    level = request.GET.get('level')
    log_type = request.GET.get('log_type')
    
    queryset = LogEntry.objects.filter(
        timestamp__gte=since,
        id__gt=last_id
    )
    
    if level:
        queryset = queryset.filter(level=level)
    if log_type:
        queryset = queryset.filter(log_type=log_type)
    
    # 限制返回数量，避免数据过多
    queryset = queryset.order_by('timestamp')[:50]
    
    serializer = LogEntrySerializer(queryset, many=True)
    
    return Response({
        'logs': serializer.data,
        'last_id': queryset.last().id if queryset.exists() else last_id,
        'timestamp': datetime.now().isoformat()
    })