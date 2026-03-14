from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Alert, AlertRule, NotificationLog
from .forms import AlertFilterForm, AlertActionForm


class AlertListView(LoginRequiredMixin, ListView):
    """报警历史列表视图"""
    model = Alert
    template_name = 'alerts/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Alert.objects.all()
        
        # 应用筛选条件
        form = AlertFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data['alert_type']:
                queryset = queryset.filter(alert_type=form.cleaned_data['alert_type'])
            
            if form.cleaned_data['severity']:
                queryset = queryset.filter(severity=form.cleaned_data['severity'])
            
            if form.cleaned_data['status']:
                queryset = queryset.filter(status=form.cleaned_data['status'])
            
            if form.cleaned_data['start_date']:
                queryset = queryset.filter(created_at__date__gte=form.cleaned_data['start_date'])
            
            if form.cleaned_data['end_date']:
                queryset = queryset.filter(created_at__date__lte=form.cleaned_data['end_date'])
            
            if form.cleaned_data['search']:
                search_term = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(title__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(location__icontains=search_term)
                )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AlertFilterForm(self.request.GET)
        
        # 统计信息
        queryset = self.get_queryset()
        context['total_count'] = queryset.count()
        context['active_count'] = queryset.filter(status='active').count()
        context['resolved_count'] = queryset.filter(status='resolved').count()
        
        return context


class AlertDetailView(LoginRequiredMixin, DetailView):
    """报警详情视图"""
    model = Alert
    template_name = 'alerts/alert_detail.html'
    context_object_name = 'alert'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取通知日志
        context['notifications'] = self.object.notifications.all()
        
        # 操作表单
        context['action_form'] = AlertActionForm()
        
        return context


@login_required
def alert_action(request, pk):
    """报警操作处理"""
    alert = get_object_or_404(Alert, pk=pk)
    
    if request.method == 'POST':
        form = AlertActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data['notes']
            
            if action == 'acknowledge':
                alert.acknowledge(request.user.username)
                messages.success(request, '报警已确认')
            
            elif action == 'resolve':
                alert.resolve(request.user.username, notes)
                messages.success(request, '报警已解决')
            
            elif action == 'false_positive':
                alert.mark_false_positive(request.user.username)
                messages.success(request, '已标记为误报')
            
            return redirect('alerts:detail', pk=pk)
    
    return redirect('alerts:detail', pk=pk)


@login_required
def api_alert_list(request):
    """报警列表API"""
    try:
        # 分页参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # 筛选参数
        alert_type = request.GET.get('alert_type')
        severity = request.GET.get('severity')
        status = request.GET.get('status')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        search = request.GET.get('search')
        
        # 构建查询
        queryset = Alert.objects.all()
        
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if status:
            queryset = queryset.filter(status=status)
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
        
        # 分页
        paginator = Paginator(queryset.order_by('-created_at'), page_size)
        alerts_page = paginator.get_page(page)
        
        # 序列化数据
        alerts_data = []
        for alert in alerts_page:
            alerts_data.append({
                'id': alert.id,
                'alert_type': alert.alert_type,
                'alert_type_display': alert.get_alert_type_display(),
                'severity': alert.severity,
                'severity_display': alert.get_severity_display(),
                'status': alert.status,
                'status_display': alert.get_status_display(),
                'title': alert.title,
                'description': alert.description,
                'location': alert.location,
                'camera_id': alert.camera_id,
                'detection_confidence': alert.detection_confidence,
                'video_clip_path': alert.video_clip_path,
                'screenshot_path': alert.screenshot_path,
                'acknowledged_by': alert.acknowledged_by,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'resolved_by': alert.resolved_by,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'created_at': alert.created_at.isoformat(),
                'duration_seconds': alert.duration.total_seconds(),
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'alerts': alerts_data,
                'pagination': {
                    'current_page': alerts_page.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': alerts_page.has_next(),
                    'has_previous': alerts_page.has_previous(),
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取报警列表失败: {str(e)}'
        }, status=500)


@login_required
def api_alert_detail(request, pk):
    """报警详情API"""
    try:
        alert = get_object_or_404(Alert, pk=pk)
        
        # 获取通知日志
        notifications = []
        for notification in alert.notifications.all():
            notifications.append({
                'id': notification.id,
                'channel': notification.channel,
                'channel_display': notification.get_channel_display(),
                'recipient': notification.recipient,
                'status': notification.status,
                'status_display': notification.get_status_display(),
                'message_content': notification.message_content,
                'error_message': notification.error_message,
                'retry_count': notification.retry_count,
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                'created_at': notification.created_at.isoformat(),
            })
        
        alert_data = {
            'id': alert.id,
            'alert_type': alert.alert_type,
            'alert_type_display': alert.get_alert_type_display(),
            'severity': alert.severity,
            'severity_display': alert.get_severity_display(),
            'status': alert.status,
            'status_display': alert.get_status_display(),
            'title': alert.title,
            'description': alert.description,
            'location': alert.location,
            'camera_id': alert.camera_id,
            'detection_confidence': alert.detection_confidence,
            'video_clip_path': alert.video_clip_path,
            'screenshot_path': alert.screenshot_path,
            'metadata': alert.metadata,
            'acknowledged_by': alert.acknowledged_by,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'resolved_by': alert.resolved_by,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'resolution_notes': alert.resolution_notes,
            'created_at': alert.created_at.isoformat(),
            'updated_at': alert.updated_at.isoformat(),
            'duration_seconds': alert.duration.total_seconds(),
            'notifications': notifications,
        }
        
        return JsonResponse({
            'success': True,
            'data': alert_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取报警详情失败: {str(e)}'
        }, status=500)


@login_required
def api_alert_statistics(request):
    """报警统计API"""
    try:
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # 按日期统计
        daily_stats = Alert.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            total=Count('id'),
            fall_alerts=Count('id', filter=Q(alert_type='fall')),
            unattended_alerts=Count('id', filter=Q(alert_type='unattended_stove')),
            active=Count('id', filter=Q(status='active')),
            resolved=Count('id', filter=Q(status='resolved')),
        ).order_by('date')
        
        # 按类型统计
        type_stats = Alert.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).values('alert_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 按严重程度统计
        severity_stats = Alert.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).values('severity').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return JsonResponse({
            'success': True,
            'data': {
                'daily_stats': list(daily_stats),
                'type_stats': list(type_stats),
                'severity_stats': list(severity_stats),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取报警统计失败: {str(e)}'
        }, status=500)