from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q
from datetime import datetime, timedelta
import json

from .models import SystemStatus, DetectionStatistics, PerformanceMetrics
from ..alerts.models import Alert
from kitchen_safety_system.database.cache_manager import CacheManager


class DashboardView(LoginRequiredMixin, TemplateView):
    """系统监控仪表板"""
    template_name = 'monitoring/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取最新系统状态
        latest_status = SystemStatus.objects.first()
        context['system_status'] = latest_status
        
        # 获取今日统计
        today = timezone.now().date()
        today_stats = DetectionStatistics.objects.filter(date=today).first()
        context['today_stats'] = today_stats
        
        # 获取最近24小时的报警
        last_24h = timezone.now() - timedelta(hours=24)
        recent_alerts = Alert.objects.filter(
            created_at__gte=last_24h
        ).order_by('-created_at')[:10]
        context['recent_alerts'] = recent_alerts
        
        # 获取系统运行时间
        if latest_status:
            context['uptime_display'] = latest_status.uptime_display
        
        return context


@login_required
def api_system_status(request):
    """获取系统状态API"""
    try:
        # 检查是否禁用Redis
        import os
        redis_disabled = os.environ.get('REDIS_DISABLED', 'false').lower() == 'true'
        
        cached_status = None
        if not redis_disabled:
            # 只有在Redis未禁用时才尝试使用缓存
            cache_manager = CacheManager()
            cached_status = cache_manager.get_system_status()
        
        if cached_status:
            return JsonResponse({
                'success': True,
                'data': cached_status
            })
        
        # 从数据库获取最新状态
        latest_status = SystemStatus.objects.first()
        if latest_status:
            status_data = {
                'status': latest_status.status,
                'status_display': latest_status.get_status_display(),
                'cpu_usage': latest_status.cpu_usage,
                'memory_usage': latest_status.memory_usage,
                'disk_usage': latest_status.disk_usage,
                'detection_fps': latest_status.detection_fps,
                'active_cameras': latest_status.active_cameras,
                'last_detection_time': latest_status.last_detection_time.isoformat() if latest_status.last_detection_time else None,
                'uptime_seconds': latest_status.uptime_seconds,
                'uptime_display': latest_status.uptime_display,
                'created_at': latest_status.created_at.isoformat(),
            }
            
            # 只有在Redis未禁用时才缓存状态数据
            if not redis_disabled:
                cache_manager.cache_system_status(status_data)
            
            return JsonResponse({
                'success': True,
                'data': status_data
            })
        else:
            return JsonResponse({
                'success': False,
                'message': '未找到系统状态数据'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取系统状态失败: {str(e)}'
        }, status=500)


@login_required
def api_detection_statistics(request):
    """获取检测统计API"""
    try:
        days = int(request.GET.get('days', 7))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        stats = DetectionStatistics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
        
        data = []
        for stat in stats:
            data.append({
                'date': stat.date.isoformat(),
                'total_detections': stat.total_detections,
                'person_detections': stat.person_detections,
                'stove_detections': stat.stove_detections,
                'fire_detections': stat.fire_detections,
                'fall_alerts': stat.fall_alerts,
                'unattended_alerts': stat.unattended_alerts,
                'total_alerts': stat.total_alerts,
                'false_positives': stat.false_positives,
                'avg_detection_confidence': stat.avg_detection_confidence,
                'processing_time_ms': stat.processing_time_ms,
                'alert_rate': stat.alert_rate,
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取检测统计失败: {str(e)}'
        }, status=500)


@login_required
def api_performance_metrics(request):
    """获取性能指标API"""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        metrics = PerformanceMetrics.objects.filter(
            timestamp__gte=start_time
        ).order_by('timestamp')
        
        data = []
        for metric in metrics:
            data.append({
                'timestamp': metric.timestamp.isoformat(),
                'detection_latency_ms': metric.detection_latency_ms,
                'frame_processing_time_ms': metric.frame_processing_time_ms,
                'queue_size': metric.queue_size,
                'memory_usage_mb': metric.memory_usage_mb,
                'gpu_usage_percent': metric.gpu_usage_percent,
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取性能指标失败: {str(e)}'
        }, status=500)


@login_required
def api_dashboard_summary(request):
    """获取仪表板摘要信息"""
    try:
        # 今日统计
        today = timezone.now().date()
        today_stats = DetectionStatistics.objects.filter(date=today).first()
        
        # 最近24小时报警统计
        last_24h = timezone.now() - timedelta(hours=24)
        alert_counts = Alert.objects.filter(created_at__gte=last_24h).aggregate(
            total=Count('id'),
            fall_alerts=Count('id', filter=Q(alert_type='fall')),
            unattended_alerts=Count('id', filter=Q(alert_type='unattended_stove'))
        )
        
        # 系统状态
        latest_status = SystemStatus.objects.first()
        
        # 平均性能指标（最近1小时）
        last_hour = timezone.now() - timedelta(hours=1)
        avg_performance = PerformanceMetrics.objects.filter(
            timestamp__gte=last_hour
        ).aggregate(
            avg_latency=Avg('detection_latency_ms'),
            avg_processing_time=Avg('frame_processing_time_ms'),
            avg_memory=Avg('memory_usage_mb'),
            avg_gpu=Avg('gpu_usage_percent')
        )
        
        summary = {
            'system_status': {
                'status': latest_status.status if latest_status else 'unknown',
                'status_display': latest_status.get_status_display() if latest_status else '未知',
                'uptime_display': latest_status.uptime_display if latest_status else '00:00:00',
                'detection_fps': latest_status.detection_fps if latest_status else 0,
                'active_cameras': latest_status.active_cameras if latest_status else 0,
            },
            'today_stats': {
                'total_detections': today_stats.total_detections if today_stats else 0,
                'total_alerts': today_stats.total_alerts if today_stats else 0,
                'fall_alerts': today_stats.fall_alerts if today_stats else 0,
                'unattended_alerts': today_stats.unattended_alerts if today_stats else 0,
                'avg_confidence': today_stats.avg_detection_confidence if today_stats else 0,
            },
            'recent_alerts': {
                'total_24h': alert_counts['total'] or 0,
                'fall_24h': alert_counts['fall_alerts'] or 0,
                'unattended_24h': alert_counts['unattended_alerts'] or 0,
            },
            'performance': {
                'avg_latency_ms': round(avg_performance['avg_latency'] or 0, 2),
                'avg_processing_time_ms': round(avg_performance['avg_processing_time'] or 0, 2),
                'avg_memory_mb': round(avg_performance['avg_memory'] or 0, 2),
                'avg_gpu_percent': round(avg_performance['avg_gpu'] or 0, 2),
            }
        }
        
        return JsonResponse({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取仪表板摘要失败: {str(e)}'
        }, status=500)