from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
import json
import os
import threading

from .models import VideoUpload, DetectionResult
from .forms import VideoUploadForm


class VideoUploadListView(LoginRequiredMixin, ListView):
    """视频上传列表"""
    model = VideoUpload
    template_name = 'video_test/list.html'
    context_object_name = 'videos'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = VideoUpload.objects.all()
        
        # 搜索
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # 状态筛选
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = VideoUpload.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context


class VideoUploadDetailView(LoginRequiredMixin, DetailView):
    """视频上传详情"""
    model = VideoUpload
    template_name = 'video_test/detail.html'
    context_object_name = 'video'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取检测结果统计
        video = self.get_object()
        results = DetectionResult.objects.filter(video_upload=video)
        
        context['total_results'] = results.count()
        context['fall_events'] = results.filter(fall_detected=True).count()
        context['unattended_events'] = results.filter(unattended_stove=True).count()
        
        # 获取最近的检测结果
        context['recent_results'] = results[:10]
        
        return context


class VideoUploadCreateView(LoginRequiredMixin, CreateView):
    """视频上传"""
    model = VideoUpload
    form_class = VideoUploadForm
    template_name = 'video_test/upload.html'
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        
        # 获取文件信息
        video_file = form.cleaned_data['video_file']
        form.instance.file_size = video_file.size
        
        response = super().form_valid(form)
        
        messages.success(self.request, f'视频 "{self.object.title}" 上传成功！')
        return response
    
    def get_success_url(self):
        return f'/video-test/{self.object.pk}/'


@login_required
def start_processing(request, pk):
    """开始处理视频"""
    video = get_object_or_404(VideoUpload, pk=pk)
    
    if video.status != 'uploaded':
        return JsonResponse({'error': '视频状态不允许处理'}, status=400)
    
    # 开始处理
    video.start_processing()
    
    # 在后台线程中处理视频
    thread = threading.Thread(target=process_video_async, args=(video.pk,))
    thread.daemon = True
    thread.start()
    
    return JsonResponse({'success': True, 'message': '开始处理视频'})


@login_required
def processing_progress(request, pk):
    """获取处理进度"""
    video = get_object_or_404(VideoUpload, pk=pk)
    
    return JsonResponse({
        'status': video.status,
        'progress': video.progress,
        'processed_frames': video.processed_frames,
        'total_frames': video.total_frames,
        'processing_time': str(video.processing_time) if video.processing_time else None
    })


@login_required
def detection_results_api(request, pk):
    """获取检测结果API"""
    video = get_object_or_404(VideoUpload, pk=pk)
    results = DetectionResult.objects.filter(video_upload=video)
    
    # 分页
    page = int(request.GET.get('page', 1))
    paginator = Paginator(results, 50)
    page_obj = paginator.get_page(page)
    
    data = {
        'results': [
            {
                'frame_number': result.frame_number,
                'timestamp': result.timestamp,
                'persons': result.persons,
                'stoves': result.stoves,
                'fires': result.fires,
                'fall_detected': result.fall_detected,
                'unattended_stove': result.unattended_stove,
                'max_confidence': result.max_confidence,
            }
            for result in page_obj
        ],
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages,
        'current_page': page,
    }
    
    return JsonResponse(data)


def process_video_async(video_pk):
    """异步处理视频"""
    try:
        video = VideoUpload.objects.get(pk=video_pk)
        
        # 模拟视频处理过程
        import time
        import random
        
        # 模拟获取视频信息
        video.total_frames = random.randint(300, 1800)  # 10-60秒的视频
        video.fps = 30.0
        video.duration = video.total_frames / video.fps
        video.resolution = "1920x1080"
        video.save()
        
        # 模拟逐帧处理
        for frame_num in range(0, video.total_frames, 10):  # 每10帧处理一次
            if video.status != 'processing':  # 检查是否被取消
                break
            
            # 模拟检测结果
            persons = []
            stoves = []
            fires = []
            
            # 随机生成检测结果
            if random.random() > 0.3:  # 70%概率检测到人
                persons.append({
                    'bbox': [random.randint(100, 500), random.randint(100, 400), 
                            random.randint(600, 900), random.randint(500, 800)],
                    'confidence': round(random.uniform(0.7, 0.95), 2)
                })
            
            if random.random() > 0.5:  # 50%概率检测到灶台
                stoves.append({
                    'bbox': [random.randint(800, 1200), random.randint(400, 600), 
                            random.randint(1300, 1600), random.randint(700, 900)],
                    'confidence': round(random.uniform(0.8, 0.98), 2)
                })
            
            if random.random() > 0.8:  # 20%概率检测到火焰
                fires.append({
                    'bbox': [random.randint(900, 1100), random.randint(450, 550), 
                            random.randint(1200, 1400), random.randint(650, 750)],
                    'confidence': round(random.uniform(0.6, 0.9), 2)
                })
            
            # 检测事件
            fall_detected = random.random() > 0.95  # 5%概率跌倒
            unattended_stove = len(stoves) > 0 and len(persons) == 0  # 有灶台无人员
            
            # 保存检测结果
            max_confidence = 0
            for detections in [persons, stoves, fires]:
                for detection in detections:
                    max_confidence = max(max_confidence, detection['confidence'])
            
            DetectionResult.objects.create(
                video_upload=video,
                frame_number=frame_num,
                timestamp=frame_num / video.fps,
                persons=persons,
                stoves=stoves,
                fires=fires,
                fall_detected=fall_detected,
                unattended_stove=unattended_stove,
                max_confidence=max_confidence
            )
            
            # 更新统计
            video.processed_frames = frame_num
            video.progress = int((frame_num / video.total_frames) * 100)
            
            if persons:
                video.person_detections += len(persons)
            if stoves:
                video.stove_detections += len(stoves)
            if fires:
                video.fire_detections += len(fires)
            if fall_detected:
                video.fall_events += 1
            if unattended_stove:
                video.unattended_events += 1
            
            video.save()
            
            # 模拟处理时间
            time.sleep(0.1)
        
        # 完成处理
        video.complete_processing()
        video.detection_log = f"处理完成：共处理 {video.total_frames} 帧，检测到 {video.person_detections} 次人员，{video.stove_detections} 次灶台，{video.fire_detections} 次火焰"
        video.save()
        
    except Exception as e:
        try:
            video = VideoUpload.objects.get(pk=video_pk)
            video.fail_processing(f"处理失败：{str(e)}")
        except:
            pass