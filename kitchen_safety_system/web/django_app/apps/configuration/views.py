from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, CreateView
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.conf import settings
import json
import os
import uuid
from datetime import datetime

from .models import SystemConfiguration, ConfigurationHistory, DetectionThreshold, CameraConfiguration
from .forms import SystemConfigurationForm, DetectionThresholdForm, CameraConfigurationForm
from kitchen_safety_system.database.cache_manager import CacheManager


def is_admin(user):
    """检查用户是否为管理员"""
    return user.is_authenticated and hasattr(user, 'is_admin') and user.is_admin


class ConfigurationListView(LoginRequiredMixin, ListView):
    """系统配置列表视图"""
    model = SystemConfiguration
    template_name = 'configuration/list.html'
    context_object_name = 'configurations'
    
    def get_queryset(self):
        category = self.request.GET.get('category')
        queryset = SystemConfiguration.objects.all()
        if category:
            queryset = queryset.filter(category=category)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 按分类分组配置
        configurations_by_category = {}
        for config in context['configurations']:
            category = config.get_category_display() if hasattr(config, 'get_category_display') else config.category
            if category not in configurations_by_category:
                configurations_by_category[category] = []
            configurations_by_category[category].append(config)
        
        context['configurations_by_category'] = configurations_by_category
        
        return context


class ConfigurationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """系统配置更新视图"""
    model = SystemConfiguration
    form_class = SystemConfigurationForm
    template_name = 'configuration/config_edit.html'
    success_url = reverse_lazy('configuration:list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        # 记录变更历史
        old_value = self.object.value
        new_value = form.cleaned_data['value']
        
        if old_value != new_value:
            ConfigurationHistory.objects.create(
                configuration=self.object,
                old_value=old_value,
                new_value=new_value,
                changed_by=self.request.user.username,
                change_reason=form.cleaned_data.get('change_reason', '')
            )
            
            # 更新缓存
            cache_manager = CacheManager()
            cache_manager.invalidate_system_config()
        
        self.object.updated_by = self.request.user.username
        messages.success(self.request, f'配置 "{self.object.name}" 已更新')
        
        return super().form_valid(form)


class DetectionThresholdListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """检测阈值列表视图"""
    model = DetectionThreshold
    template_name = 'configuration/threshold_list.html'
    context_object_name = 'thresholds'
    
    def test_func(self):
        return is_admin(self.request.user)


class DetectionThresholdUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """检测阈值更新视图"""
    model = DetectionThreshold
    form_class = DetectionThresholdForm
    template_name = 'configuration/threshold_edit.html'
    success_url = reverse_lazy('configuration:thresholds')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'检测阈值 "{self.object.name}" 已更新')
        
        # 清除相关缓存
        cache_manager = CacheManager()
        cache_manager.invalidate_detection_config()
        
        return super().form_valid(form)


class CameraConfigurationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """摄像头配置列表视图"""
    model = CameraConfiguration
    template_name = 'configuration/camera_list.html'
    context_object_name = 'cameras'
    
    def test_func(self):
        return is_admin(self.request.user)


class CameraConfigurationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """摄像头配置创建视图"""
    model = CameraConfiguration
    form_class = CameraConfigurationForm
    template_name = 'configuration/camera_edit.html'
    success_url = reverse_lazy('configuration:cameras')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'摄像头 "{form.instance.name}" 已创建')
        return super().form_valid(form)


class CameraConfigurationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """摄像头配置更新视图"""
    model = CameraConfiguration
    form_class = CameraConfigurationForm
    template_name = 'configuration/camera_edit.html'
    success_url = reverse_lazy('configuration:cameras')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'摄像头 "{self.object.name}" 已更新')
        return super().form_valid(form)


@login_required
@user_passes_test(is_admin)
def api_get_configuration(request, key):
    """获取单个配置API"""
    try:
        config = get_object_or_404(SystemConfiguration, key=key)
        
        return JsonResponse({
            'success': True,
            'data': {
                'key': config.key,
                'name': config.name,
                'category': config.category,
                'config_type': config.config_type,
                'value': config.get_typed_value(),
                'default_value': config.default_value,
                'description': config.description,
                'is_editable': config.is_editable,
                'requires_restart': config.requires_restart,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin)
def api_update_configuration(request, key):
    """更新单个配置API"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': '只支持POST请求'
        }, status=405)
    
    try:
        config = get_object_or_404(SystemConfiguration, key=key)
        
        if not config.is_editable:
            return JsonResponse({
                'success': False,
                'message': '此配置不可编辑'
            }, status=400)
        
        data = json.loads(request.body)
        new_value = data.get('value')
        change_reason = data.get('change_reason', '')
        
        # 验证新值
        is_valid, error_message = config.validate_value(new_value)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'message': f'配置值无效: {error_message}'
            }, status=400)
        
        # 记录变更历史
        old_value = config.value
        if str(old_value) != str(new_value):
            ConfigurationHistory.objects.create(
                configuration=config,
                old_value=old_value,
                new_value=str(new_value),
                changed_by=request.user.username,
                change_reason=change_reason
            )
            
            # 更新配置
            config.set_typed_value(new_value)
            config.updated_by = request.user.username
            config.save()
            
            # 清除缓存
            cache_manager = CacheManager()
            cache_manager.invalidate_system_config()
            
            return JsonResponse({
                'success': True,
                'message': '配置已更新',
                'requires_restart': config.requires_restart
            })
        else:
            return JsonResponse({
                'success': True,
                'message': '配置值未发生变化'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '无效的JSON数据'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新配置失败: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin)
def api_get_all_configurations(request):
    """获取所有配置API"""
    try:
        category = request.GET.get('category')
        
        queryset = SystemConfiguration.objects.all()
        if category:
            queryset = queryset.filter(category=category)
        
        configurations = {}
        for config in queryset:
            configurations[config.key] = {
                'name': config.name,
                'category': config.category,
                'config_type': config.config_type,
                'value': config.get_typed_value(),
                'default_value': config.default_value,
                'description': config.description,
                'is_editable': config.is_editable,
                'requires_restart': config.requires_restart,
                'updated_at': config.updated_at.isoformat(),
                'updated_by': config.updated_by,
            }
        
        return JsonResponse({
            'success': True,
            'data': configurations
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin)
def api_get_detection_thresholds(request):
    """获取检测阈值API"""
    try:
        thresholds = DetectionThreshold.objects.filter(is_enabled=True)
        
        data = {}
        for threshold in thresholds:
            data[threshold.name] = {
                'detection_type': threshold.detection_type,
                'confidence_threshold': threshold.confidence_threshold,
                'time_threshold_seconds': threshold.time_threshold_seconds,
                'distance_threshold_meters': threshold.distance_threshold_meters,
                'additional_params': threshold.additional_params,
                'description': threshold.description,
            }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取检测阈值失败: {str(e)}'
        }, status=500)


@login_required
def api_get_camera_configurations(request):
    """获取摄像头配置API"""
    try:
        cameras = CameraConfiguration.objects.filter(is_enabled=True)
        
        data = []
        for camera in cameras:
            data.append({
                'camera_id': camera.camera_id,
                'name': camera.name,
                'location': camera.location,
                'rtsp_url': camera.rtsp_url,
                'resolution_width': camera.resolution_width,
                'resolution_height': camera.resolution_height,
                'fps': camera.fps,
                'detection_zones': camera.detection_zones,
                'calibration_data': camera.calibration_data,
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取摄像头配置失败: {str(e)}'
        }, status=500)


@login_required
def api_upload_video(request):
    """视频上传API"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': '只支持POST请求'
        }, status=405)
    
    try:
        if 'video' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': '未找到视频文件'
            }, status=400)
        
        video_file = request.FILES['video']
        description = request.POST.get('description', '')
        
        # 验证文件类型
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        file_extension = os.path.splitext(video_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'message': f'不支持的文件格式。支持的格式: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # 验证文件大小 (100MB)
        max_size = 100 * 1024 * 1024
        if video_file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': '文件大小不能超过100MB'
            }, status=400)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_extension}"
        
        # 创建上传目录
        upload_dir = 'test_videos'
        upload_path = os.path.join(settings.MEDIA_ROOT, upload_dir)
        os.makedirs(upload_path, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_dir, filename)
        saved_path = default_storage.save(file_path, video_file)
        
        # 获取文件信息
        full_path = os.path.join(settings.MEDIA_ROOT, saved_path)
        file_size = os.path.getsize(full_path)
        
        # 尝试获取视频信息 (需要ffmpeg或类似工具)
        video_info = get_video_info(full_path)
        
        # 构建响应数据
        response_data = {
            'file_id': file_id,
            'filename': video_file.name,
            'saved_filename': filename,
            'file_size': format_file_size(file_size),
            'file_path': saved_path,
            'file_url': f"{settings.MEDIA_URL}{saved_path}",
            'description': description,
            'upload_time': datetime.now().isoformat(),
            'duration': video_info.get('duration'),
            'resolution': video_info.get('resolution'),
            'fps': video_info.get('fps'),
        }
        
        # 记录上传日志
        try:
            from kitchen_safety_system.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.info(f"视频上传成功: {video_file.name} -> {saved_path} (用户: {request.user.username})")
        except:
            pass
        
        return JsonResponse({
            'success': True,
            'message': '视频上传成功',
            'data': response_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }, status=500)


@login_required
def api_update_all_configurations(request):
    """批量更新配置API"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': '只支持POST请求'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        
        updated_configs = []
        errors = []
        
        # 处理检测配置
        if 'detection' in data:
            detection_config = data['detection']
            config_updates = [
                ('fall_confidence_threshold', detection_config.get('fall_confidence')),
                ('stove_distance_threshold', detection_config.get('stove_distance')),
                ('unattended_time_threshold', detection_config.get('unattended_time')),
            ]
            
            for key, value in config_updates:
                if value is not None:
                    try:
                        config, created = SystemConfiguration.objects.get_or_create(
                            key=key,
                            defaults={
                                'name': key.replace('_', ' ').title(),
                                'category': 'detection',
                                'config_type': 'float' if 'confidence' in key or 'distance' in key else 'integer',
                                'value': str(value),
                                'is_editable': True,
                                'updated_by': request.user.username
                            }
                        )
                        if not created:
                            config.value = str(value)
                            config.updated_by = request.user.username
                            config.save()
                        updated_configs.append(key)
                    except Exception as e:
                        errors.append(f'{key}: {str(e)}')
        
        # 处理报警配置
        if 'alerts' in data:
            alerts_config = data['alerts']
            config_updates = [
                ('email_notifications_enabled', alerts_config.get('email_enabled')),
                ('sms_notifications_enabled', alerts_config.get('sms_enabled')),
                ('sound_alerts_enabled', alerts_config.get('sound_enabled')),
                ('alert_email_address', alerts_config.get('alert_email')),
            ]
            
            for key, value in config_updates:
                if value is not None:
                    try:
                        config, created = SystemConfiguration.objects.get_or_create(
                            key=key,
                            defaults={
                                'name': key.replace('_', ' ').title(),
                                'category': 'alerts',
                                'config_type': 'boolean' if 'enabled' in key else 'string',
                                'value': str(value),
                                'is_editable': True,
                                'updated_by': request.user.username
                            }
                        )
                        if not created:
                            config.value = str(value)
                            config.updated_by = request.user.username
                            config.save()
                        updated_configs.append(key)
                    except Exception as e:
                        errors.append(f'{key}: {str(e)}')
        
        # 处理视频配置
        if 'video' in data:
            video_config = data['video']
            config_updates = [
                ('save_video_clips', video_config.get('save_clips')),
                ('video_clip_duration', video_config.get('clip_duration')),
                ('max_storage_days', video_config.get('max_storage_days')),
            ]
            
            for key, value in config_updates:
                if value is not None:
                    try:
                        config, created = SystemConfiguration.objects.get_or_create(
                            key=key,
                            defaults={
                                'name': key.replace('_', ' ').title(),
                                'category': 'video',
                                'config_type': 'boolean' if 'save_' in key else 'integer',
                                'value': str(value),
                                'is_editable': True,
                                'updated_by': request.user.username
                            }
                        )
                        if not created:
                            config.value = str(value)
                            config.updated_by = request.user.username
                            config.save()
                        updated_configs.append(key)
                    except Exception as e:
                        errors.append(f'{key}: {str(e)}')
        
        # 清除缓存
        try:
            cache_manager = CacheManager()
            cache_manager.invalidate_config_cache()
        except:
            pass
        
        if errors:
            return JsonResponse({
                'success': False,
                'message': f'部分配置更新失败: {"; ".join(errors)}',
                'updated_configs': updated_configs
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': f'成功更新 {len(updated_configs)} 个配置',
            'updated_configs': updated_configs
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '无效的JSON数据'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新配置失败: {str(e)}'
        }, status=500)


def get_video_info(file_path):
    """获取视频文件信息"""
    try:
        # 这里可以使用ffmpeg-python或其他库来获取视频信息
        # 为了简化，这里返回基本信息
        import subprocess
        
        # 尝试使用ffprobe获取视频信息
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                
                # 提取视频流信息
                video_stream = None
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                        break
                
                if video_stream:
                    duration = float(info.get('format', {}).get('duration', 0))
                    width = video_stream.get('width', 0)
                    height = video_stream.get('height', 0)
                    fps = eval(video_stream.get('r_frame_rate', '0/1'))
                    
                    return {
                        'duration': f"{int(duration // 60)}:{int(duration % 60):02d}",
                        'resolution': f"{width}x{height}" if width and height else None,
                        'fps': f"{fps:.1f}" if fps > 0 else None
                    }
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # 如果ffprobe不可用，返回基本信息
        return {
            'duration': None,
            'resolution': None,
            'fps': None
        }
        
    except Exception:
        return {
            'duration': None,
            'resolution': None,
            'fps': None
        }


def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"