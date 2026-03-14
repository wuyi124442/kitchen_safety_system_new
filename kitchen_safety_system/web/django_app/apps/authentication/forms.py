from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserProfile


class LoginForm(forms.Form):
    """登录表单"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '用户名',
            'required': True
        }),
        label='用户名'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '密码',
            'required': True
        }),
        label='密码'
    )


class UserRegistrationForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '邮箱地址'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '姓'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '名'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '电话号码'
        })
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '部门'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'department', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': '用户名'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': '密码'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': '确认密码'})


class UserProfileForm(forms.ModelForm):
    """用户配置表单"""
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'notification_email', 'notification_sms', 'dashboard_refresh_interval']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'notification_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dashboard_refresh_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 60,
                'step': 1
            }),
        }
        labels = {
            'avatar': '头像',
            'notification_email': '邮件通知',
            'notification_sms': '短信通知',
            'dashboard_refresh_interval': '仪表板刷新间隔(秒)',
        }


class UserEditForm(forms.ModelForm):
    """用户编辑表单（管理员使用）"""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'department', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': '用户名',
            'email': '邮箱',
            'first_name': '姓',
            'last_name': '名',
            'phone': '电话',
            'department': '部门',
            'role': '角色',
            'is_active': '激活状态',
        }