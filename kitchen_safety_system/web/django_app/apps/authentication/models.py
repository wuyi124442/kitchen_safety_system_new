from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """扩展用户模型"""
    
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('operator', '操作员'),
        ('viewer', '查看者'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        verbose_name='用户角色'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='电话号码'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='部门'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'auth_user_extended'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_operator(self):
        return self.role in ['admin', 'operator']
    
    @property
    def can_configure_system(self):
        return self.role == 'admin'


class UserProfile(models.Model):
    """用户配置文件"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='用户'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='头像'
    )
    notification_email = models.BooleanField(
        default=True,
        verbose_name='邮件通知'
    )
    notification_sms = models.BooleanField(
        default=False,
        verbose_name='短信通知'
    )
    dashboard_refresh_interval = models.IntegerField(
        default=5,
        verbose_name='仪表板刷新间隔(秒)'
    )
    
    class Meta:
        verbose_name = '用户配置'
        verbose_name_plural = '用户配置'
        db_table = 'user_profile'
    
    def __str__(self):
        return f"{self.user.username}的配置"