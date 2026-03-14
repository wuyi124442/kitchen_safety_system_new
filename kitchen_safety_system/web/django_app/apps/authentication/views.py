from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import User, UserProfile
from .forms import LoginForm, UserProfileForm


class LoginView(TemplateView):
    """用户登录视图"""
    template_name = 'authentication/login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('monitoring:dashboard')
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'monitoring:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, '用户名或密码错误')
        
        return render(request, self.template_name, {'form': form})


@login_required
def logout_view(request):
    """用户登出"""
    logout(request)
    messages.success(request, '您已成功登出')
    return redirect('authentication:login')


class ProfileView(LoginRequiredMixin, UpdateView):
    """用户配置视图"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'authentication/profile.html'
    success_url = reverse_lazy('authentication:profile')
    
    def get_object(self, queryset=None):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, '配置已更新')
        return super().form_valid(form)


@method_decorator(csrf_exempt, name='dispatch')
class APILoginView(TemplateView):
    """API登录视图"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': '用户名和密码不能为空'
                }, status=400)
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': '登录成功',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'role': user.role,
                        'is_admin': user.is_admin,
                        'is_operator': user.is_operator,
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '用户名或密码错误'
                }, status=401)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '无效的JSON数据'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'登录失败: {str(e)}'
            }, status=500)


@login_required
def api_logout_view(request):
    """API登出视图"""
    logout(request)
    return JsonResponse({
        'success': True,
        'message': '登出成功'
    })


@login_required
def api_user_info(request):
    """获取当前用户信息"""
    user = request.user
    profile = getattr(user, 'profile', None)
    
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'role_display': user.get_role_display(),
            'department': user.department,
            'phone': user.phone,
            'is_admin': user.is_admin,
            'is_operator': user.is_operator,
            'can_configure_system': user.can_configure_system,
            'profile': {
                'notification_email': profile.notification_email if profile else True,
                'notification_sms': profile.notification_sms if profile else False,
                'dashboard_refresh_interval': profile.dashboard_refresh_interval if profile else 5,
            } if profile else None
        }
    })